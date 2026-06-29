"""Incentive form generation: rationalization suggestions & dissatisfaction corrective actions.

Fixed 10 pairs per enterprise (not per employee). Template content is read
sequentially from ``json文件/incentive-forms.json``; employees are randomly
sampled from active regular (non-manager) staff at generation time.
"""
from __future__ import annotations

import json
import logging
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.models.employee import Employee
from app.services.hr_generator import (
    DocGenResult,
    _add_enterprise,
    _pre_check_and_render,
    find_department_head_name,
    find_general_manager_name,
    find_hr_manager_name,
)
from app.services.signature import SignatureStore, signature_render_value
from app.templates.loader import TemplateLoader

logger = logging.getLogger(__name__)

INCENTIVE_FORMS_JSON = (
    Path(__file__).parent.parent.parent.parent / "json文件" / "incentive-forms.json"
)

TMPL_SUGGESTION = "20员工激励__2024年度员工满意度调查分析报告-xls__1合理化建议表"
TMPL_DISSATISFACTION = (
    "20员工激励__2024年度员工满意度调查分析报告-xls__员工不满意项目纠正和预防措施表"
)

FIXED_PAIR_COUNT = 10


def load_incentive_pairs(json_path: Path | None = None) -> list[dict[str, Any]]:
    """Load paired suggestion/dissatisfaction records in sequential order."""
    path = json_path or INCENTIVE_FORMS_JSON
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs = data.get("pairs", [])
    if len(pairs) < FIXED_PAIR_COUNT:
        logger.warning(
            "incentive-forms.json has %d pairs, expected %d",
            len(pairs),
            FIXED_PAIR_COUNT,
        )
    return pairs[:FIXED_PAIR_COUNT]


def _fmt_date(raw: str | date | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, date):
        return raw.strftime("%Y年%m月%d日")
    text = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y年%m月%d日")
        except ValueError:
            continue
    return text


def _regular_employee_pool(employees: list[Employee]) -> list[Employee]:
    return [
        e
        for e in employees
        if e.employment_status in ("在职", "")
        and e.is_regular_employee
        and not e.is_manager
    ]


def _pick_employees(pool: list[Employee], count: int) -> list[Employee]:
    if not pool:
        return []
    if len(pool) >= count:
        return random.sample(pool, count)
    return [random.choice(pool) for _ in range(count)]


def _build_context(
    emp: Employee,
    doc_date: date,
    incentive: dict[str, Any],
    seq: int,
    enterprise: dict[str, Any],
    employees: list[Employee] | None = None,
    sig_store: SignatureStore | None = None,
) -> dict[str, Any]:
    emp_ctx = emp.to_namespace_dict()
    # Add employee's signature to context
    if sig_store is not None:
        emp_ctx["signature"] = signature_render_value(emp.name, sig_store)

    ctx: dict[str, Any] = {
        "employee": emp_ctx,
        "document": {
            "date": _fmt_date(doc_date),
            "year": str(doc_date.year),
            "month": str(doc_date.month),
            "seq_no": str(seq).zfill(2),
        },
        "incentive": dict(incentive),
    }

    # Fill in personnel for dissatisfaction corrective action form
    if employees is not None and "dissatisfaction_description" in incentive:
        dept_head = find_department_head_name(emp.department_name, employees) or emp.name
        hr_mgr = find_hr_manager_name(employees) or find_general_manager_name(employees) or emp.name
        ctx["incentive"].update({
            "analyst_name": signature_render_value(dept_head, sig_store) if sig_store else dept_head,
            "analyst_date": _fmt_date(doc_date + timedelta(days=3)),
            "action_owner": signature_render_value(dept_head, sig_store) if sig_store else dept_head,
            "action_date": _fmt_date(doc_date + timedelta(days=7)),
            "implementer_name": signature_render_value(emp.name, sig_store) if sig_store else emp.name,
            "implementer_date": _fmt_date(doc_date + timedelta(days=14)),
            "verifier_name": signature_render_value(hr_mgr, sig_store) if sig_store else hr_mgr,
            "verifier_date": _fmt_date(doc_date + timedelta(days=21)),
        })

    _add_enterprise(ctx, enterprise)
    return ctx


def generate_incentive_forms(
    employees: list[Employee],
    loader: TemplateLoader,
    enterprise: dict[str, Any],
    sig_store: SignatureStore,
    json_path: Path | None = None,
) -> list[DocGenResult]:
    """Generate exactly 10 suggestion forms + 10 dissatisfaction forms (1:1 paired)."""
    pairs = load_incentive_pairs(json_path)
    pool = _regular_employee_pool(employees)
    if not pool:
        logger.warning("No regular non-manager employees available for incentive forms")
        pool = [e for e in employees if e.employment_status in ("在职", "")]

    suggestion_employees = _pick_employees(pool, len(pairs))
    dissatisfaction_employees = _pick_employees(pool, len(pairs))

    tmpl_suggestion = loader.get_by_id(TMPL_SUGGESTION)
    tmpl_dissatisfaction = loader.get_by_id(TMPL_DISSATISFACTION)

    results: list[DocGenResult] = []
    for idx, pair in enumerate(pairs):
        seq = pair.get("seq", idx + 1)
        doc_raw = pair.get("document_date", f"2024-{idx + 1:02d}-15")
        doc_date = datetime.strptime(str(doc_raw), "%Y-%m-%d").date()

        suggestion = pair.get("suggestion", {})
        dissatisfaction = pair.get("dissatisfaction", {})

        if idx < len(suggestion_employees):
            ctx = _build_context(
                suggestion_employees[idx], doc_date, suggestion, seq, enterprise,
                sig_store=sig_store,
            )
            results.append(_pre_check_and_render(tmpl_suggestion, ctx))

        if idx < len(dissatisfaction_employees):
            ctx = _build_context(
                dissatisfaction_employees[idx], doc_date, dissatisfaction, seq, enterprise,
                employees=employees,
                sig_store=sig_store,
            )
            results.append(_pre_check_and_render(tmpl_dissatisfaction, ctx))

    return results
