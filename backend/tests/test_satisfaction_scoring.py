"""Tests for satisfaction survey scoring."""
from __future__ import annotations

from app.services.satisfaction_scoring import (
    OVERALL_SATISFACTION,
    REPORT_ITEM_SCORES,
    SURVEY_FORM_TARGETS,
    build_survey_mark_context,
    compute_aggregate_stats,
    generate_respondent_scores,
)


def test_generate_respondent_scores_match_item_targets() -> None:
    keys = [f"emp{i}" for i in range(48)]
    scores = generate_respondent_scores(keys, SURVEY_FORM_TARGETS)
    stats = compute_aggregate_stats(scores)

    assert len(scores) == 48
    assert all(len(row) == 50 for row in scores.values())
    assert all(1 <= s <= 5 for row in scores.values() for s in row)
    assert stats.deviation_from(SURVEY_FORM_TARGETS) <= 0.05
    assert 3.45 <= stats.overall <= 3.60


def test_survey_mark_context_places_single_checkmark() -> None:
    ctx = build_survey_mark_context([5, 3])
    assert ctx["q01_c5"] == "√"
    assert ctx["q01_c4"] == ""
    assert ctx["q02_c3"] == "√"
    assert ctx["q02_c5"] == ""


def test_report_reference_scores_average_near_overall() -> None:
    avg = round(sum(REPORT_ITEM_SCORES) / len(REPORT_ITEM_SCORES), 2)
    assert 3.45 <= avg <= 3.60
    assert OVERALL_SATISFACTION == 3.52
