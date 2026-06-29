"""HR document generation rules.

Tasks 7.1 – 7.4:
  7.1  Onboarding documents (须知/登记表/合同, date = hire_date)
  7.2  Probation-end documents (培训评价/转正申请/技能履历, date = probation_end_date)
  7.3  Satisfaction survey (per employee per year)
  7.4  Pre-generation placeholder check; per-document gap reporting
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.core.calendar import WorkCalendar, probation_end_date
from app.models.employee import Employee
from app.services.renderer import (
    ContextMap,
    build_output_filename,
    render_template,
)
from app.services.satisfaction_scoring import (
    build_survey_mark_context,
    generate_respondent_scores,
)
from app.services.signature import SignatureStore, signature_render_value
from app.templates.loader import TemplateMeta, TemplateLoader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template ID constants (from meta.yaml)
# ---------------------------------------------------------------------------

# Onboarding documents
TMPL_NOTICE = "16员工档案__员工档案文件资料-xlsx__2新员工入职需知"
TMPL_REGISTER = "16员工档案__员工档案文件资料-xlsx__3公司入职人员登记表"
TMPL_CONTRACT = "16员工档案__员工档案文件资料-xlsx__4用工合同协议书"

# Probation documents
TMPL_TRAIN_EVAL = "16员工档案__员工档案文件资料-xlsx__5新员工入职岗位培训评价表"
TMPL_PROBATION_APP = "16员工档案__员工档案文件资料-xlsx__6转正申请表"
TMPL_SKILL_RESUME = "16员工档案__员工档案文件资料-xlsx__7技能履历个人管理表"

# Satisfaction survey
TMPL_SATISFACTION = "20员工激励__2024年度员工满意度调查分析报告-xls__员工满意度调查表"
TMPL_SATISFACTION_REPORT = (
    "20员工激励__2024年度员工满意度调查分析报告-xls__员工满意度调查分析报告"
)

# Employee roster (company-level, all employees in one document)
TMPL_ROSTER = "16员工档案__员工档案文件资料-xlsx__8人员花名册"

ONBOARDING_TEMPLATES = [TMPL_NOTICE, TMPL_REGISTER, TMPL_CONTRACT]
PROBATION_TEMPLATES = [TMPL_TRAIN_EVAL, TMPL_PROBATION_APP, TMPL_SKILL_RESUME]

HR_DEPT_KEYWORDS = ("综管部", "综合管理部", "行政管理部")
TRAINING_DEPT_KEYWORDS = ("培训部", "培训科", "培训中心")
HR_DEPT_DISPLAY = "综管部"

MANAGER_POSITION_KEYWORDS = ("经理", "主任", "主管", "负责人")
GENERAL_MANAGER_KEYWORDS = ("总经理",)
SYSTEM_EXPERT_KEYWORDS = ("体系专员", "体系工程师", "文控")
TRAINING_STAFF_KEYWORDS = ("培训",)

ONBOARDING_TRAINING_ITEMS: list[tuple[str, str]] = [
    ("企业文化培训", "企业简介及企业发展历程培训"),
    ("规章制度培训", "员工手册内容培训及考核激励制度内容的培训"),
    ("企业环境培训", "环境及职业健康安全的培训"),
    ("岗位知识内容培训", "岗位职责、作业流程、操作规程及质量标准培训与考核"),
]


def is_hr_department(department_name: str) -> bool:
    dept = department_name.strip()
    return any(keyword in dept for keyword in HR_DEPT_KEYWORDS)


def _active_employees(employees: list[Employee]) -> list[Employee]:
    return [emp for emp in employees if emp.employment_status in ("在职", "")]


def _matches_position_keywords(position_name: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in position_name for keyword in keywords)


def _pick_by_manager_priority(candidates: list[Employee]) -> str:
    if not candidates:
        return ""

    managers = [emp for emp in candidates if emp.is_manager]
    if managers:
        return managers[0].name

    for keyword in MANAGER_POSITION_KEYWORDS:
        for emp in candidates:
            if keyword in emp.position_name:
                return emp.name

    return candidates[0].name


def find_hr_manager_name(employees: list[Employee]) -> str:
    """Return the HR manager name from roster (综管部), preferring managers."""
    hr_staff = [emp for emp in _active_employees(employees) if is_hr_department(emp.department_name)]
    if not hr_staff:
        return ""
    return _pick_by_manager_priority(hr_staff)


def find_general_manager_name(employees: list[Employee]) -> str:
    """Return the general manager name from roster."""
    active = _active_employees(employees)
    for keyword in GENERAL_MANAGER_KEYWORDS:
        exact = [
            emp for emp in active
            if emp.position_name.strip() == keyword
            or (keyword in emp.position_name and "副" not in emp.position_name)
        ]
        if exact:
            return exact[0].name
    return ""


def find_department_head_name(
    department_name: str,
    employees: list[Employee],
    *,
    exclude_name: str = "",
) -> str:
    """Return the department head for *department_name* from roster."""
    dept = department_name.strip()
    if not dept:
        return ""

    same_dept = [
        emp for emp in _active_employees(employees)
        if emp.department_name.strip() == dept and emp.name.strip() != exclude_name.strip()
    ]
    if not same_dept:
        return ""

    managers = [emp for emp in same_dept if emp.is_manager]
    if managers:
        return managers[0].name

    for keyword in MANAGER_POSITION_KEYWORDS:
        for emp in same_dept:
            if keyword in emp.position_name:
                return emp.name

    return ""


def find_training_plan_preparer_name(employees: list[Employee]) -> str:
    """Return 年培训计划编制人：优先体系专员，其次培训部门人员。"""
    active = _active_employees(employees)

    system_experts = [
        emp for emp in active
        if _matches_position_keywords(emp.position_name, SYSTEM_EXPERT_KEYWORDS)
    ]
    if system_experts:
        return system_experts[0].name

    training_dept = [
        emp for emp in active
        if any(keyword in emp.department_name for keyword in TRAINING_DEPT_KEYWORDS)
    ]
    if training_dept:
        return _pick_by_manager_priority(training_dept)

    training_staff = [
        emp for emp in active
        if _matches_position_keywords(emp.position_name, TRAINING_STAFF_KEYWORDS)
    ]
    if training_staff:
        return training_staff[0].name

    return ""


def build_onboarding_training_list_data(
    emp: Employee,
    calendar: WorkCalendar | None,
    trainer_name: str,
    hr_department: str = HR_DEPT_DISPLAY,
) -> dict[str, list[ContextMap]]:
    """Build list rows for the onboarding training evaluation table."""
    cal = calendar or WorkCalendar()
    rows: list[ContextMap] = []
    for index, (category, content) in enumerate(ONBOARDING_TRAINING_ITEMS):
        training_date = cal.add_working_days(emp.hire_date, index)
        rows.append({
            "onboarding": {
                "category": category,
                "content": content,
                "date": _fmt(training_date),
                "department": hr_department,
                "trainer": trainer_name,
                "conclusion": "合格",
                "meets_requirement": "是",
            }
        })
    return {"onboarding_training_rows": rows}


def build_roster_list_data(employees: list[Employee]) -> dict[str, list[ContextMap]]:
    """Build list rows for the employee roster table (one row per active employee)."""
    rows: list[ContextMap] = []
    for emp in employees:
        if emp.employment_status not in ("在职", ""):
            continue
        rows.append({"employee": emp.to_namespace_dict()})
    return {"employee_rows": rows}


def resolve_manager_map(
    manager_map: dict[str, str] | None,
    all_employees: list[Employee] | None,
) -> dict[str, str]:
    """Merge explicit manager_map with roster-derived management signatures."""
    resolved = dict(manager_map or {})
    if not all_employees:
        return resolved

    if "hr_manager" not in resolved:
        hr_name = find_hr_manager_name(all_employees)
        if hr_name:
            resolved["hr_manager"] = hr_name

    if "general_manager" not in resolved:
        gm_name = find_general_manager_name(all_employees)
        if gm_name:
            resolved["general_manager"] = gm_name

    gm_name = resolved.get("general_manager", "")

    if "prepared_by" not in resolved:
        preparer = find_training_plan_preparer_name(all_employees)
        if preparer:
            resolved["prepared_by"] = preparer

    if "reviewed_by" not in resolved and gm_name:
        resolved["reviewed_by"] = gm_name

    if "approved_by" not in resolved and gm_name:
        resolved["approved_by"] = gm_name

    return resolved


def resolve_employee_manager_map(
    emp: Employee,
    manager_map: dict[str, str] | None,
    all_employees: list[Employee] | None,
) -> dict[str, str]:
    """Resolve company-wide and per-employee signature roles for *emp*."""
    resolved = resolve_manager_map(manager_map, all_employees)
    if "department_head" not in resolved and all_employees:
        head = find_department_head_name(
            emp.department_name,
            all_employees,
            exclude_name=emp.name,
        )
        if head:
            resolved["department_head"] = head
        elif resolved.get("general_manager"):
            resolved["department_head"] = resolved["general_manager"]
    return resolved


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------


def _fmt(d: date | None) -> str:
    if d is None:
        return ""
    return d.strftime("%Y年%m月%d日")


def _build_employee_context(emp: Employee, doc_date: date | None = None) -> ContextMap:
    ctx: ContextMap = {
        "employee": emp.to_namespace_dict(),
        "document": {
            "date": _fmt(doc_date),
            "year": str(doc_date.year) if doc_date else "",
            "month": str(doc_date.month) if doc_date else "",
        },
    }
    return ctx


def _add_enterprise(ctx: ContextMap, enterprise: dict[str, Any]) -> ContextMap:
    ctx["enterprise"] = enterprise
    return ctx


def _add_signature(
    ctx: ContextMap,
    emp: Employee,
    store: SignatureStore,
    manager_map: dict[str, str] | None = None,
) -> ContextMap:
    ctx["employee"]["signature"] = signature_render_value(emp.name, store)
    if manager_map:
        ctx["signature"] = {
            role: signature_render_value(name, store)
            for role, name in manager_map.items()
        }
    return ctx


# ---------------------------------------------------------------------------
# 7.4  Pre-check helper
# ---------------------------------------------------------------------------


@dataclass
class DocGenResult:
    template_id: str
    output_filename: str
    html: str = ""
    pdf_bytes: bytes = b""
    missing_keys: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""

    @property
    def ok(self) -> bool:
        return not self.skipped and not self.missing_keys


def _pre_check_and_render(
    tmpl: TemplateMeta | None,
    context: ContextMap,
    list_data: dict | None = None,
) -> DocGenResult:
    """Render *tmpl* with *context*, pre-checking required placeholders.

    Returns a :class:`DocGenResult`; sets ``skipped=True`` when the template
    is not found or has fatal missing required keys.
    """
    if tmpl is None:
        return DocGenResult(
            template_id="unknown",
            output_filename="",
            skipped=True,
            skip_reason="Template not found in loader",
        )

    html, missing = render_template(tmpl, context, list_data)
    filename = build_output_filename(tmpl.output_naming, context)

    if missing:
        logger.warning(
            "Template %s has %d missing keys: %s",
            tmpl.id,
            len(missing),
            missing,
        )

    return DocGenResult(
        template_id=tmpl.id,
        output_filename=filename,
        html=html,
        missing_keys=missing,
    )


# ---------------------------------------------------------------------------
# 7.1  Onboarding documents
# ---------------------------------------------------------------------------


def generate_onboarding_docs(
    emp: Employee,
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
    manager_map: dict[str, str] | None = None,
) -> list[DocGenResult]:
    """Generate 须知, 登记表, 合同 for *emp* at their hire date."""
    doc_date = emp.hire_date
    results: list[DocGenResult] = []
    for tmpl_id in ONBOARDING_TEMPLATES:
        tmpl = loader.get_by_id(tmpl_id)
        ctx = _build_employee_context(emp, doc_date)
        _add_enterprise(ctx, enterprise)
        _add_signature(ctx, emp, sig_store, manager_map)
        results.append(_pre_check_and_render(tmpl, ctx))
    return results


# ---------------------------------------------------------------------------
# 7.2  Probation documents
# ---------------------------------------------------------------------------


def generate_probation_docs(
    emp: Employee,
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
    calendar: WorkCalendar | None = None,
    manager_map: dict[str, str] | None = None,
    all_employees: list[Employee] | None = None,
) -> list[DocGenResult]:
    """Generate 培训评价, 转正申请, 技能履历 for *emp* at their probation end date."""
    cal = calendar or WorkCalendar()
    resolved_manager_map = resolve_employee_manager_map(emp, manager_map, all_employees)
    trainer_name = resolved_manager_map.get("hr_manager", "")

    p_date = probation_end_date(
        emp.hire_date,
        is_regular_employee=emp.is_regular_employee,
        calendar=cal,
    )
    emp.probation_end_date = p_date
    doc_date = p_date

    results: list[DocGenResult] = []
    for tmpl_id in PROBATION_TEMPLATES:
        tmpl = loader.get_by_id(tmpl_id)
        ctx = _build_employee_context(emp, doc_date)
        _add_enterprise(ctx, enterprise)
        _add_signature(
            ctx,
            emp,
            sig_store,
            resolved_manager_map or None,
        )
        list_data = None
        if tmpl_id == TMPL_TRAIN_EVAL:
            list_data = build_onboarding_training_list_data(
                emp,
                cal,
                trainer_name,
            )
        results.append(_pre_check_and_render(tmpl, ctx, list_data))
    return results


# ---------------------------------------------------------------------------
# 7.3  Satisfaction survey (per employee per year)
# ---------------------------------------------------------------------------


def generate_satisfaction_surveys(
    employees: list[Employee],
    years: list[int],
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
) -> list[DocGenResult]:
    """Generate one satisfaction survey per active employee per year."""
    tmpl = loader.get_by_id(TMPL_SATISFACTION)
    results: list[DocGenResult] = []
    active = [emp for emp in employees if emp.employment_status in ("在职", "")]
    for year in years:
        respondent_keys = [f"{emp.name}:{year}" for emp in active]
        all_scores = generate_respondent_scores(respondent_keys)
        for emp in active:
            key = f"{emp.name}:{year}"
            doc_date = date(year, 6, 30)
            ctx = _build_employee_context(emp, doc_date)
            _add_enterprise(ctx, enterprise)
            _add_signature(ctx, emp, sig_store)
            ctx["document"]["year"] = str(year)
            ctx["incentive"] = {"survey_year": str(year)}
            ctx["survey"] = build_survey_mark_context(all_scores[key])
            results.append(_pre_check_and_render(tmpl, ctx))
    return results


def generate_satisfaction_analysis_reports(
    years: list[int],
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
    employees: list[Employee] | None = None,
) -> list[DocGenResult]:
    """Generate one company-level satisfaction analysis report per year."""
    from app.services.satisfaction_scoring import build_analysis_report_context

    tmpl = loader.get_by_id(TMPL_SATISFACTION_REPORT)
    results: list[DocGenResult] = []
    hr_manager = find_hr_manager_name(employees or []) if employees else ""

    for year in years:
        context, list_data = build_analysis_report_context(
            survey_year=year,
            survey_month="6",
            report_date=f"{year}年7月5日",
            enterprise_name=enterprise.get("name", ""),
            hr_manager=signature_render_value(hr_manager, sig_store) if hr_manager else "",
        )
        results.append(_pre_check_and_render(tmpl, context, list_data))
    return results


# ---------------------------------------------------------------------------
# Employee roster (company-level)
# ---------------------------------------------------------------------------


def generate_roster(
    employees: list[Employee],
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    doc_date: date | None = None,
) -> DocGenResult:
    """Generate one roster document listing all active employees with row.index 1..N."""
    tmpl = loader.get_by_id(TMPL_ROSTER)
    doc_date = doc_date or date.today()
    ctx: ContextMap = {
        "enterprise": enterprise,
        "document": {
            "date": _fmt(doc_date),
            "year": str(doc_date.year),
            "month": str(doc_date.month),
        },
    }
    list_data = build_roster_list_data(employees)
    return _pre_check_and_render(tmpl, ctx, list_data)


# ---------------------------------------------------------------------------
# Full HR doc generation for one employee
# ---------------------------------------------------------------------------


def generate_all_hr_docs(
    emp: Employee,
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
    years: list[int],
    calendar: WorkCalendar | None = None,
    manager_map: dict[str, str] | None = None,
    all_employees: list[Employee] | None = None,
) -> list[DocGenResult]:
    """Generate all HR documents for a single employee."""
    resolved_manager_map = resolve_manager_map(manager_map, all_employees)
    results: list[DocGenResult] = []
    results.extend(
        generate_onboarding_docs(
            emp,
            loader,
            enterprise,
            sig_store,
            resolved_manager_map or None,
        )
    )
    results.extend(
        generate_probation_docs(
            emp,
            loader,
            enterprise,
            sig_store,
            calendar,
            resolved_manager_map or None,
            all_employees,
        )
    )
    return results
