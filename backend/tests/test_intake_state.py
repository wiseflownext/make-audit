"""Regression tests for shared intake session state."""
from __future__ import annotations

from app.api import intake
from app.models.intake_parser import parse_intake
from app.models.intake_template import generate_intake_template


def test_upload_mutates_shared_state_objects():
    """Upload must mutate shared dict/list objects, not rebind module globals."""
    intake._enterprise.clear()
    intake._employees.clear()
    enterprise_ref = intake._enterprise
    employees_ref = intake._employees

    content = generate_intake_template()
    enterprise, employees = parse_intake(content, filename="intake.xlsx")

    intake._enterprise.clear()
    intake._enterprise.update(enterprise)
    intake._employees.clear()
    intake._employees.extend(intake._employees_to_dicts(employees))

    assert intake._enterprise is enterprise_ref
    assert intake._employees is employees_ref
    assert intake._enterprise.get("name") == "浙江精创汽车零部件有限公司"
    assert len(intake._employees) == 52
