"""Tests for standardized sample roster data."""
from __future__ import annotations

from app.models.sample_roster_data import (
    POSITION_CATEGORIES,
    SAMPLE_EMPLOYEES,
    get_sample_roster_rows,
    get_sample_roster_summary,
)


def test_sample_roster_has_52_employees():
    assert len(SAMPLE_EMPLOYEES) == 52
    assert len(get_sample_roster_rows()) == 52


def test_sample_roster_category_distribution():
    summary = get_sample_roster_summary()
    assert summary["生产"] == 28
    assert summary["品质"] == 10
    assert summary["技术"] == 8
    assert summary["管理"] == 6
    assert set(summary) == set(POSITION_CATEGORIES)


def test_sample_roster_internal_auditors_and_operators():
    auditors = [e for e in SAMPLE_EMPLOYEES if e.is_internal_auditor == "是"]
    operators = [e for e in SAMPLE_EMPLOYEES if e.position_name == "操作工"]
    assert len(auditors) == 7
    assert len(operators) == 21
