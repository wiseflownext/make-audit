"""Tests for incentive form generation."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from app.models.employee import Employee
from app.services.incentive_generator import (
    FIXED_PAIR_COUNT,
    load_incentive_pairs,
    generate_incentive_forms,
)
from app.templates.loader import TemplateLoader

TEMPLATE_BASE = Path(__file__).parent.parent.parent / "template"


def _sample_employees(n: int = 15) -> list[Employee]:
    return [
        Employee(
            name=f"员工{i}",
            department_name="生产部" if i % 2 else "质量部",
            position_name="操作工",
            hire_date=date(2023, 1, 10),
            is_regular_employee=True,
            is_manager=False,
        )
        for i in range(1, n + 1)
    ]


def test_load_incentive_pairs_count() -> None:
    pairs = load_incentive_pairs()
    assert len(pairs) == FIXED_PAIR_COUNT
    assert pairs[0]["seq"] == 1
    assert "suggestion" in pairs[0]
    assert "dissatisfaction" in pairs[0]


def test_generate_incentive_forms_produces_twenty_docs() -> None:
    loader = TemplateLoader(TEMPLATE_BASE)
    employees = _sample_employees()
    enterprise = {"name": "测试汽配有限公司"}
    results = generate_incentive_forms(employees, loader, enterprise, sig_store=None)  # type: ignore[arg-type]

    assert len(results) == 20
    suggestion = [r for r in results if "合理化建议表" in r.output_filename]
    dissatisfaction = [r for r in results if "员工不满意项目" in r.output_filename]
    assert len(suggestion) == 10
    assert len(dissatisfaction) == 10
    assert all(r.ok for r in results)
    assert "机加工区域刀具摆放标准化" in suggestion[0].html
