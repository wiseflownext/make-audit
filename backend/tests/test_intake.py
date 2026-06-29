"""Tests for combined intake Excel parsing."""
from __future__ import annotations

import pytest

from app.models.intake_parser import IntakeValidationError, parse_intake
from app.models.intake_template import generate_intake_template


def test_parse_combined_intake_template():
    content = generate_intake_template()
    enterprise, employees = parse_intake(content, filename="intake.xlsx")
    assert enterprise["name"] == "浙江精创汽车零部件有限公司"
    assert enterprise["year"] == "2025"
    assert len(employees) == 52
    assert employees[0].name == "陈建国"
    assert employees[0].position_category == "管理"
    assert employees[-1].name == "吕超"
    assert employees[-1].position_name == "操作工"

    categories = {emp.position_category for emp in employees}
    assert categories == {"生产", "品质", "技术", "管理"}
    auditors = [e for e in employees if e.is_internal_auditor]
    assert len(auditors) >= 5
    operators = [e for e in employees if e.position_name == "操作工"]
    assert len(operators) == 21


def test_parse_intake_rejects_csv():
    with pytest.raises(IntakeValidationError, match="Excel"):
        parse_intake(b"name,dept\n", filename="data.csv")


def test_parse_intake_rejects_single_sheet():
    from io import BytesIO

    import openpyxl

    wb = openpyxl.Workbook()
    buf = BytesIO()
    wb.save(buf)
    with pytest.raises(IntakeValidationError, match="两个工作表"):
        parse_intake(buf.getvalue(), filename="single.xlsx")
