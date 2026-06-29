"""Incentive form generation: rationalization suggestions & dissatisfaction corrective actions.

Fixed 10 pairs per enterprise (not per employee). Template content is read
sequentially from ``json文件/incentive-forms.json``; employees are randomly
sampled from active regular (non-manager) staff at generation time.
"""
from __future__ import annotations

import json
import logging
import random
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.models.employee import Employee
from app.services.hr_generator import DocGenResult, _add_enterprise, _pre_check_and_render
from app.services.signature import SignatureStore
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
) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "employee": emp.to_namespace_dict(),
        "document": {
            "date": _fmt_date(doc_date),
            "year": str(doc_date.year),
            "month": str(doc_date.month),
            "seq_no": str(seq).zfill(2),
        },
        "incentive": dict(incentive),
    }
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
                suggestion_employees[idx], doc_date, suggestion, seq, enterprise
            )
            results.append(_pre_check_and_render(tmpl_suggestion, ctx))

        if idx < len(dissatisfaction_employees):
            ctx = _build_context(
                dissatisfaction_employees[idx], doc_date, dissatisfaction, seq, enterprise
            )
            results.append(_pre_check_and_render(tmpl_dissatisfaction, ctx))

    return results
