"""Training record generation and linkage.

Tasks 8.1 – 8.7:
  8.1  Load training-plan-comprehensive.json
  8.2  Annual training plan table generation (3 years)
  8.3  Target-audience → employee-set matching
  8.4  TrainingSession objects as single source of truth
  8.5  Attendance record per session
  8.6  Personal training record (per employee per year)
  8.7  Consistency validation
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from app.core.calendar import WorkCalendar, calendar_for_years
from app.models.employee import Employee
from app.services.renderer import ContextMap, render_template, build_output_filename
from app.services.hr_generator import (
    DocGenResult,
    _pre_check_and_render,
    find_department_head_name,
    find_general_manager_name,
    find_hr_manager_name,
    resolve_manager_map,
)
from app.services.signature import SignatureStore, signature_render_value
from app.templates.loader import TemplateLoader

logger = logging.getLogger(__name__)

TRAINING_EFFECTIVENESS_EVALUATION = (
    "本次培训按计划完成，参训人员出勤率100%，经考核及现场提问，"
    "参训人员均已理解并掌握培训内容，达到预期培训目标，培训有效。"
)

TMPL_ANNUAL_PLAN = "18培训计划__培训计划__2025-年培训计划表-xls__2024年培训计划"

# 面向对象 → 解析讲师时优先参考的部门
AUDIENCE_DEPT_HINTS: dict[str, str] = {
    "检验员、实验员": "品质部",
    "生产员工/质量员工": "品质部",
    "技术质量人员": "技术部",
    "市场部员工": "市场部",
    "销售部员工": "销售部",
    "操作工": "生产部",
    "检验员": "品质部",
    "库管员": "生产部",
    "内审员": "品质部",
    "内审员/VDA6.3过程审核": "品质部",
    "管理人员": "综合管理部",
}

# 岗位/角色标签 → 解析函数键
TRAINER_ROLE_LABELS = frozenset({
    "综管部主管", "各部门主管", "各部门负责人", "出纳",
    "市场部负责人", "销售部负责人", "质量部负责人",
    "总经理", "管理层", "技术部", "车间主任", "委外",
})

_TRAINING_TIME_RE = re.compile(
    r"^(\d{1,2})\.(\d{1,2})-(\d{1,2})\.(\d{1,2})$"
)

# ---------------------------------------------------------------------------
# 8.1  Load training plan JSON
# ---------------------------------------------------------------------------

TRAINING_PLAN_JSON = Path(__file__).parent.parent.parent.parent / "json文件" / "training-plan-comprehensive.json"


def load_training_plan(json_path: Path | None = None) -> dict[str, Any]:
    path = json_path or TRAINING_PLAN_JSON
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 8.3  Target-audience → employee mapping
# ---------------------------------------------------------------------------

AUDIENCE_RULES: dict[str, str] = {
    "全体员工": "all",
    "新进员工": "new_employee",
    "管理人员": "managers",
    "内审员": "internal_auditors",
    "内审员/VDA6.3过程审核": "internal_auditors",
    "操作工": "position:操作工",
    "检验员": "position:检验员",
    "检验员、实验员": "position:检验员|实验员",
    "库管员": "position:库管员",
    "销售部员工": "department:销售部",
    "市场部员工": "department:市场部",
    "技术质量人员": "department:技术部|品质部",
    "生产员工/质量员工": "department:生产部|品质部",
    "生产/技术/质量": "department:生产部|技术部|品质部",
}


def match_employees(
    target_audience: str,
    employees: list[Employee],
    hire_date_cutoff: date | None = None,
) -> list[Employee]:
    """Return employees matching *target_audience*."""
    rule = AUDIENCE_RULES.get(target_audience.strip(), "")
    if not rule:
        # Unknown audience → log and return all for safety
        logger.warning("Unknown training audience %r, defaulting to all employees.", target_audience)
        return list(employees)

    if rule == "all":
        return [e for e in employees if e.employment_status in ("在职", "")]

    if rule == "new_employee":
        if hire_date_cutoff:
            return [e for e in employees if e.hire_date >= hire_date_cutoff]
        return list(employees)

    if rule == "managers":
        return [e for e in employees if e.is_manager]

    if rule == "internal_auditors":
        return [e for e in employees if e.is_internal_auditor]

    if rule.startswith("position:"):
        positions = set(rule.split(":", 1)[1].split("|"))
        return [e for e in employees if e.position_name in positions or
                any(p in e.position_name for p in positions)]

    if rule.startswith("department:"):
        depts = set(rule.split(":", 1)[1].split("|"))
        return [e for e in employees if e.department_name in depts or
                any(d in e.department_name for d in depts)]

    return list(employees)


# ---------------------------------------------------------------------------
# 8.4  TrainingSession
# ---------------------------------------------------------------------------


@dataclass
class TrainingSession:
    course_name: str
    plan_type: str          # "annual" | "new_employee"
    target_audience: str
    trainer: str
    duration: str
    location: str
    assessment_method: str
    content: str
    scheduled_date: date
    year: int
    attendees: list[Employee] = field(default_factory=list)
    session_idx: int = 0    # sequence within year


# ---------------------------------------------------------------------------
# 8.2  Annual training plan generation
# ---------------------------------------------------------------------------


def _active_employees(employees: list[Employee]) -> list[Employee]:
    return [e for e in employees if e.employment_status in ("在职", "")]


def _find_by_position_keyword(
    employees: list[Employee],
    keyword: str,
    *,
    department_name: str = "",
) -> str:
    candidates = _active_employees(employees)
    if department_name:
        candidates = [
            e for e in candidates
            if e.department_name.strip() == department_name.strip()
        ]
    for emp in candidates:
        if keyword in emp.position_name:
            return emp.name
    return ""


def _find_finance_staff(employees: list[Employee]) -> str:
    for keyword in ("出纳", "财务主管", "财务"):
        name = _find_by_position_keyword(employees, keyword)
        if name:
            return name
    return find_department_head_name("综合管理部", employees)


def _find_workshop_director(employees: list[Employee]) -> str:
    name = _find_by_position_keyword(employees, "车间主任")
    if name:
        return name
    return find_department_head_name("生产部", employees)


def _audience_department_hint(target_audience: str) -> str:
    return AUDIENCE_DEPT_HINTS.get(target_audience.strip(), "")


def resolve_trainer_name(
    course: dict[str, Any],
    employees: list[Employee],
) -> str:
    """Resolve a course's 讲师/记录讲师 to a concrete employee name."""
    recorded = (course.get("记录讲师") or "").strip()
    if recorded:
        return recorded

    label = (course.get("讲师") or "").strip()
    if not label:
        return ""

    if label not in TRAINER_ROLE_LABELS and not any(
        role in label for role in TRAINER_ROLE_LABELS
    ):
        return label

    audience = (course.get("面向对象") or "").strip()
    dept_hint = _audience_department_hint(audience)

    if label in ("综管部主管",):
        return find_hr_manager_name(employees)

    if label in ("总经理", "管理层"):
        return find_general_manager_name(employees)

    if label == "市场部负责人":
        return find_department_head_name("市场部", employees) or find_hr_manager_name(employees)

    if label == "销售部负责人":
        return find_department_head_name("销售部", employees) or find_hr_manager_name(employees)

    if label == "质量部负责人":
        return (
            find_department_head_name("品质部", employees)
            or find_department_head_name("质量部", employees)
        )

    if label == "技术部":
        return find_department_head_name("技术部", employees)

    if label == "车间主任":
        return _find_workshop_director(employees)

    if label == "出纳":
        return _find_finance_staff(employees)

    if label == "委外":
        return "委外"

    if label in ("各部门主管", "各部门负责人"):
        if dept_hint:
            head = find_department_head_name(dept_hint, employees)
            if head:
                return head
        return find_hr_manager_name(employees)

    return label


def parse_training_time_period(time_str: str, year: int) -> tuple[date, date] | None:
    """Parse annual-plan 培训时间 like ``3.2-3.6`` into a date range for *year*."""
    text = (time_str or "").strip()
    if not text or "入职" in text:
        return None

    match = _TRAINING_TIME_RE.match(text)
    if not match:
        return None

    sm, sd, em, ed = (int(x) for x in match.groups())
    try:
        start = date(year, sm, sd)
        end = date(year, em, ed)
    except ValueError:
        return None

    if end < start:
        return None
    return start, end


def schedule_date_in_period(
    start: date,
    end: date,
    calendar: WorkCalendar,
) -> date:
    """Return the first working day within [*start*, *end*]."""
    current = start
    while current <= end:
        if calendar.is_working_day(current):
            return current
        current += timedelta(days=1)
    return calendar.next_working_day(end)


def _schedule_date_for_course(
    course: dict[str, Any],
    year: int,
    calendar: WorkCalendar,
    fallback_index: int,
    fallback_working_days: list[date],
) -> date:
    """Schedule one annual course using 培训时间, falling back to spread dates."""
    period = parse_training_time_period(course.get("培训时间", ""), year)
    if period:
        return schedule_date_in_period(period[0], period[1], calendar)

    if fallback_working_days:
        step = max(1, len(fallback_working_days) // 40)
        day_idx = min(fallback_index * step, len(fallback_working_days) - 1)
        return fallback_working_days[day_idx]

    return date(year, 3, 1)


def _month_schedule_marks(scheduled_date: date) -> dict[str, str]:
    """Build month checkmarks (1–12) for the annual plan table."""
    month = scheduled_date.month
    marks: dict[str, str] = {}
    for m in range(1, 13):
        marks[f"month_{m}"] = "√" if m == month else ""
    return marks


def _schedule_annual_courses(
    plan_trainings: list[dict],
    year: int,
    employees: list[Employee],
    calendar: WorkCalendar,
) -> list[TrainingSession]:
    """Schedule annual plan courses on legal working days per 培训时间."""
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    working_days = calendar.working_days_in_range(year_start, year_end)

    sessions: list[TrainingSession] = []

    for idx, course in enumerate(plan_trainings):
        sched_date = _schedule_date_for_course(
            course, year, calendar, idx, working_days
        )

        audience = course.get("面向对象", "") or "全体员工"
        matched = match_employees(audience, employees)
        trainer = resolve_trainer_name(course, employees)
        sessions.append(
            TrainingSession(
                course_name=course.get("培训名称", ""),
                plan_type="annual",
                target_audience=audience,
                trainer=trainer,
                duration=course.get("时长", ""),
                location=course.get("培训地点", ""),
                assessment_method=course.get("考核方式", ""),
                content=course.get("培训内容", ""),
                scheduled_date=sched_date,
                year=year,
                attendees=matched,
                session_idx=idx + 1,
            )
        )
    return sessions


def build_sessions(
    training_plan: dict,
    employees: list[Employee],
    years: list[int],
    calendar: WorkCalendar | None = None,
) -> list[TrainingSession]:
    """Build all training sessions for *years* from the loaded training plan."""
    cal = calendar or WorkCalendar()
    annual = training_plan.get("annual_training_plan", {}).get("trainings", [])
    new_emp = training_plan.get("new_employee_training", {}).get("trainings", [])

    sessions: list[TrainingSession] = []

    for year in years:
        # Annual courses
        sessions.extend(_schedule_annual_courses(annual, year, employees, cal))

        # New employee courses: within 7 days of each employee's hire date
        for emp in employees:
            if emp.hire_date.year != year:
                continue
            for day_offset, course in enumerate(new_emp):
                sched = cal.add_working_days(emp.hire_date, day_offset)
                sessions.append(
                    TrainingSession(
                        course_name=course.get("培训名称", ""),
                        plan_type="new_employee",
                        target_audience=f"新进员工:{emp.name}",
                        trainer=resolve_trainer_name(course, employees),
                        duration=course.get("时长", ""),
                        location=course.get("培训地点", ""),
                        assessment_method=course.get("考核方式", ""),
                        content=course.get("培训内容", ""),
                        scheduled_date=sched,
                        year=year,
                        attendees=[emp],
                        session_idx=day_offset + 1,
                    )
                )

    return sessions


# ---------------------------------------------------------------------------
# 8.5  Attendance record per session
# ---------------------------------------------------------------------------

TMPL_ATTENDANCE = "18培训计划__培训记录__2024年培训记录-空白表单-xlsx__培训记录"
MIN_ATTENDANCE_ROWS = 14


def build_attendance_list_data(
    attendees: list[Employee],
    sig_store: SignatureStore | None = None,
) -> dict[str, list[ContextMap]]:
    """Build attendance rows for a training session record (min 14 rows)."""
    empty_exam = {"first_score": "", "retake_score": "", "passed": "", "retrain": ""}
    rows: list[ContextMap] = []
    for emp in attendees:
        emp_ctx = emp.to_namespace_dict()
        if sig_store:
            emp_ctx["signature"] = signature_render_value(emp.name, sig_store)
        rows.append({
            "employee": emp_ctx,
            "training": {"exam": dict(empty_exam)},
        })

    while len(rows) < MIN_ATTENDANCE_ROWS:
        rows.append({
            "employee": {"name": "", "department_name": ""},
            "training": {"exam": dict(empty_exam)},
        })
    return {"attendance_rows": rows}


def generate_attendance_records(
    sessions: list[TrainingSession],
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
) -> list[DocGenResult]:
    """Generate one attendance record HTML/PDF per :class:`TrainingSession`."""
    tmpl = loader.get_by_id(TMPL_ATTENDANCE)
    results: list[DocGenResult] = []

    for session in sessions:
        ctx: ContextMap = {
            "enterprise": enterprise,
            "training": {
                "course_name": session.course_name,
                "instructor_name": session.trainer,
                "period": session.scheduled_date.strftime("%Y年%m月%d日"),
                "duration": session.duration,
                "attendance": f"{len(session.attendees)}/{len(session.attendees)}",
                "location": session.location,
                "assessment_method": session.assessment_method,
                "content": session.content,
                "evaluation": TRAINING_EFFECTIVENESS_EVALUATION,
                "exam": {"first_score": "", "retake_score": "", "passed": "", "retrain": ""},
            },
            "document": {
                "date": session.scheduled_date.strftime("%Y年%m月%d日"),
                "year": str(session.year),
            },
        }

        list_data = build_attendance_list_data(session.attendees, sig_store)
        result = _pre_check_and_render(tmpl, ctx, list_data)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# 8.2b  Annual training plan table (per year)
# ---------------------------------------------------------------------------


def generate_annual_training_plans(
    sessions: list[TrainingSession],
    years: list[int],
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
    employees: list[Employee],
    manager_map: dict[str, str] | None = None,
) -> list[DocGenResult]:
    """Generate one annual training plan table per year."""
    tmpl = loader.get_by_id(TMPL_ANNUAL_PLAN)
    results: list[DocGenResult] = []
    resolved = resolve_manager_map(manager_map, employees)

    annual_by_year: dict[int, list[TrainingSession]] = {}
    for session in sessions:
        if session.plan_type != "annual":
            continue
        annual_by_year.setdefault(session.year, []).append(session)

    for year in years:
        year_sessions = sorted(
            annual_by_year.get(year, []),
            key=lambda s: (s.session_idx, s.scheduled_date),
        )

        ctx: ContextMap = {
            "enterprise": enterprise,
            "document": {"year": str(year), "date": f"{year}年12月31日"},
            "training": {"year": str(year)},
            "signature": {
                role: signature_render_value(name, sig_store)
                for role, name in resolved.items()
            },
        }

        plan_rows: list[ContextMap] = []
        for session in year_sessions:
            month_marks = _month_schedule_marks(session.scheduled_date)
            plan_rows.append({
                "training": {
                    "course_name": session.course_name,
                    "target_audience": session.target_audience,
                    "duration": session.duration,
                    "method": "内训",
                    "organizer": "综合管理部",
                    "trainer": session.trainer,
                    "assessment_method": session.assessment_method,
                    **month_marks,
                },
                "row": {},
            })

        result = _pre_check_and_render(tmpl, ctx, list_data={"annual_plan_rows": plan_rows})
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# 8.6  Personal training record template (new) + generation
# ---------------------------------------------------------------------------

PERSONAL_TRAINING_TEMPLATE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "template"
    / "人力资源"
    / "个人培训记录表"
)


def _ensure_personal_training_template() -> None:
    """Create template files for 个人培训记录表 if they don't exist."""
    PERSONAL_TRAINING_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

    meta_path = PERSONAL_TRAINING_TEMPLATE_DIR / "meta.yaml"
    html_path = PERSONAL_TRAINING_TEMPLATE_DIR / "template.html"

    if not meta_path.exists():
        meta_path.write_text(
            """id: 人力资源__个人培训记录表
title: 个人培训记录表
status: reviewed_ready
generation_granularity: per_employee_per_year
data_sources:
  - enterprise
  - employee
  - training
prerequisites: []
output_naming: 个人培训记录-{{employee.name}}-{{document.year}}年
precheck_enabled: true
variables: []
signature_mappings: []
date_mappings: []
checkbox_mappings: []
render_mode: a4-print
""",
            encoding="utf-8",
        )

    if not html_path.exists():
        html_path.write_text(
            """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>个人培训记录表</title>
<style>
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #e5e5e5; color: #000; }
body { font-family: "SimSun", "Songti SC", "Microsoft YaHei", serif; font-size: 10.5pt; }
.page { width: 210mm; min-height: 297mm; margin: 0 auto 12px; padding: 12mm; background: #fff; box-shadow: 0 0 0 1px #bbb; }
table { width: 100%; border-collapse: collapse; }
td, th { border: 1px solid #000; padding: 1.2mm 1.4mm; vertical-align: middle; word-break: break-word; }
.center { text-align: center; }
.bold { font-weight: 700; }
@media print { html, body { background: #fff; } .page { margin: 0; box-shadow: none; } }
</style></head><body>
<div class="page">
<div class="center bold" style="font-size:14pt;margin-bottom:4mm">{{enterprise.name}}</div>
<div class="center bold" style="font-size:13pt;margin-bottom:6mm">个人培训记录表（{{document.year}}年）</div>
<table style="margin-bottom:4mm">
  <tr><td style="width:15%">姓名</td><td style="width:25%">{{employee.name}}</td>
      <td style="width:15%">部门</td><td style="width:25%">{{employee.department_name}}</td>
      <td style="width:10%">岗位</td><td>{{employee.position_name}}</td></tr>
</table>
<table>
<thead>
  <tr class="bold">
    <th style="width:5%">序号</th>
    <th style="width:22%">培训课程</th>
    <th style="width:12%">培训日期</th>
    <th style="width:8%">时长</th>
    <th style="width:10%">培训地点</th>
    <th style="width:10%">讲师</th>
    <th style="width:10%">考核方式</th>
    <th style="width:8%">成绩</th>
    <th style="width:15%">签名</th>
  </tr>
</thead>
<tbody>
<!-- LIST:training_rows -->
<tr>
  <td class="center">{{row.index}}</td>
  <td>{{training.course_name}}</td>
  <td class="center">{{training.date}}</td>
  <td class="center">{{training.duration_hours}}</td>
  <td class="center">{{training.location}}</td>
  <td class="center">{{training.trainer}}</td>
  <td class="center">{{training.assessment_method}}</td>
  <td class="center">{{training.exam.score}}</td>
  <td class="center">{{employee.signature}}</td>
</tr>
<!-- /LIST -->
</tbody>
</table>
<div style="margin-top:8mm;text-align:right">员工签名：{{employee.signature}}</div>
</div></body></html>
""",
            encoding="utf-8",
        )


def generate_personal_training_records(
    sessions: list[TrainingSession],
    employees: list[Employee],
    years: list[int],
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
) -> list[DocGenResult]:
    """Generate one personal training record per employee per year."""
    _ensure_personal_training_template()
    # Reload loader to pick up the new template
    from app.templates.loader import TemplateLoader as TL

    tmpl_id = "人力资源__个人培训记录表"
    tmpl = loader.get_by_id(tmpl_id)
    # If not loaded, create a quick on-the-fly lookup
    if tmpl is None:
        from app.templates.loader import TemplateMeta

        meta_path = PERSONAL_TRAINING_TEMPLATE_DIR / "meta.yaml"
        import yaml

        raw = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        from dataclasses import fields
        tmpl = TemplateMeta.from_yaml(meta_path, "人力资源", PERSONAL_TRAINING_TEMPLATE_DIR.parent)

    results: list[DocGenResult] = []

    # Group sessions by (employee.name, year)
    by_emp_year: dict[tuple[str, int], list[TrainingSession]] = {}
    for s in sessions:
        for emp in s.attendees:
            key = (emp.name, s.year)
            by_emp_year.setdefault(key, []).append(s)

    emp_map = {e.name: e for e in employees}

    for year in years:
        for emp in employees:
            key = (emp.name, year)
            emp_sessions = by_emp_year.get(key, [])

            ctx: ContextMap = {
                "enterprise": enterprise,
                "employee": emp.to_namespace_dict(),
                "document": {"year": str(year), "date": f"{year}年12月31日"},
            }
            ctx["employee"]["signature"] = signature_render_value(emp.name, sig_store)

            training_rows: list[ContextMap] = [
                {
                    "training": {
                        "course_name": s.course_name,
                        "date": s.scheduled_date.strftime("%Y年%m月%d日"),
                        "duration_hours": s.duration,
                        "location": s.location,
                        "trainer": s.trainer,
                        "assessment_method": s.assessment_method,
                        "exam": {"score": ""},
                    },
                    "employee": ctx["employee"],
                    "row": {},
                }
                for s in emp_sessions
            ]

            result = _pre_check_and_render(tmpl, ctx, list_data={"training_rows": training_rows})
            results.append(result)

    return results


# ---------------------------------------------------------------------------
# 8.7  Consistency check
# ---------------------------------------------------------------------------


def validate_training_consistency(
    sessions: list[TrainingSession],
    personal_records: list[DocGenResult],
    employees: list[Employee],
) -> list[str]:
    """Return a list of inconsistency messages.

    Checks that every session attendee appears in at least one personal record.
    """
    issues: list[str] = []
    emp_names = {e.name for e in employees}

    for session in sessions:
        for emp in session.attendees:
            if emp.name not in emp_names:
                issues.append(
                    f"Session '{session.course_name}' ({session.scheduled_date}) "
                    f"has attendee '{emp.name}' not found in employee list."
                )

    return issues
