"""Tests for the placeholder parser (Task 2.2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.templates.placeholder import (  # noqa: E402
    PlaceholderParser,
    Placeholder,
    PlaceholderSyntaxError,
)


def test_extract_valid_placeholders():
    html = "<p>{{enterprise.name}} 你好，{{employee.name}}</p>"
    parser = PlaceholderParser()
    result = parser.extract(html)
    assert Placeholder(namespace="enterprise", key="name") in result
    assert Placeholder(namespace="employee", key="name") in result


def test_extract_nested_key():
    html = "<span>{{training.exam.first_score}}</span>"
    parser = PlaceholderParser()
    result = parser.extract(html)
    assert Placeholder(namespace="training", key="exam.first_score") in result


def test_extract_deduplicates():
    html = "{{employee.name}} and {{employee.name}}"
    parser = PlaceholderParser()
    result = parser.extract(html)
    employee_names = [p for p in result if p.namespace == "employee" and p.key == "name"]
    assert len(employee_names) == 1


def test_detect_single_brace_anomalies():
    html = "<td>{position_safety.month_label}</td>"
    parser = PlaceholderParser()
    anomalies = parser.detect_malformed(html)
    assert len(anomalies) == 1
    assert "position_safety.month_label" in anomalies[0]


def test_no_false_positive_in_css():
    css_html = "<style>body { font-size: 12pt; }</style>"
    parser = PlaceholderParser()
    anomalies = parser.detect_malformed(css_html)
    assert len(anomalies) == 0


def test_validate_against_namespace_all_valid():
    html = "{{enterprise.name}} {{employee.name}}"
    parser = PlaceholderParser()
    known = {"enterprise", "employee", "contract", "training", "signature",
              "document", "incentive", "position_safety", "row"}
    gaps = parser.validate_namespaces(html, known)
    assert gaps == []


def test_validate_against_namespace_unknown():
    html = "{{unknown_ns.field}}"
    parser = PlaceholderParser()
    known = {"enterprise", "employee"}
    gaps = parser.validate_namespaces(html, known)
    assert len(gaps) == 1
    assert gaps[0].namespace == "unknown_ns"


def test_extract_empty_html():
    parser = PlaceholderParser()
    assert parser.extract("") == []


def test_placeholder_full_key():
    p = Placeholder(namespace="training", key="exam.first_score")
    assert p.full_key == "training.exam.first_score"
