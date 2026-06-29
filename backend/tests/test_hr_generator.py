"""Unit tests for HR document generation helpers."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from app.core.calendar import WorkCalendar
from app.models.employee import Employee
from app.models.sample_roster_data import sample_employees_as_models
from app.services.hr_generator import (
    TMPL_PROBATION_APP,
    TMPL_ROSTER,
    build_onboarding_training_list_data,
    build_roster_list_data,
    find_department_head_name,
    find_general_manager_name,
    find_hr_manager_name,
    find_training_plan_preparer_name,
    generate_probation_docs,
    generate_roster,
    resolve_employee_manager_map,
    resolve_manager_map,
)
from app.services.renderer import render_list_region
from app.services.signature import SignatureStore
from app.templates.loader import TemplateLoader


def _employee(
    name: str,
    department_name: str,
    *,
    position_name: str = "主管",
    is_manager: bool = False,
) -> Employee:
    return Employee(
        name=name,
        department_name=department_name,
        position_name=position_name,
        hire_date=date(2024, 1, 15),
        is_manager=is_manager,
    )


def test_employee_probation_period_from_hire_date() -> None:
    emp = _employee("张三", "生产部")
    ns = emp.to_namespace_dict()
    assert ns["probation_period"] == "2024年01月15日至2024年01月23日"


def test_generate_probation_app_includes_probation_period() -> None:
    template_base = Path(__file__).parent.parent.parent / "template"
    loader = TemplateLoader(template_base)
    emp = _employee("张三", "生产部")
    results = generate_probation_docs(
        emp,
        loader,
        {"name": "示例企业有限公司"},
        SignatureStore(),
        calendar=WorkCalendar(),
    )
    probation_app = next(r for r in results if r.template_id == TMPL_PROBATION_APP)
    assert "2024年01月15日至2024年01月23日" in probation_app.html
    assert "年　　月　　日至　　年　　月　　日" not in probation_app.html


def test_find_hr_manager_prefers_manager_in_hr_department() -> None:
    employees = [
        _employee("李四", "生产部"),
        _employee("王专员", "综管部", position_name="专员"),
        _employee("张主管", "综管部", position_name="综管部主管", is_manager=True),
    ]
    assert find_hr_manager_name(employees) == "张主管"


def test_find_hr_manager_matches_comprehensive_admin_department() -> None:
    employees = [_employee("赵经理", "综合管理部", position_name="经理", is_manager=True)]
    assert find_hr_manager_name(employees) == "赵经理"


def test_build_onboarding_training_rows_use_working_days_from_hire_date() -> None:
    cal = WorkCalendar()
    emp = _employee("张三", "生产部")
    rows = build_onboarding_training_list_data(emp, cal, "张主管")["onboarding_training_rows"]

    assert len(rows) == 4
    assert rows[0]["onboarding"]["date"] == "2024年01月15日"
    assert rows[1]["onboarding"]["date"] == "2024年01月16日"
    assert rows[0]["onboarding"]["department"] == "综管部"
    assert rows[0]["onboarding"]["trainer"] == "张主管"
    assert rows[0]["onboarding"]["conclusion"] == "合格"
    assert rows[0]["onboarding"]["meets_requirement"] == "是"
    assert rows[0]["onboarding"]["category"] == "企业文化培训"


def test_resolve_manager_map_fills_hr_manager_from_roster() -> None:
    employees = [_employee("张主管", "综管部", position_name="主管", is_manager=True)]
    resolved = resolve_manager_map({}, employees)
    assert resolved["hr_manager"] == "张主管"


def test_find_general_manager_from_roster() -> None:
    employees = sample_employees_as_models()
    assert find_general_manager_name(employees) == "陈建国"


def test_find_training_plan_preparer_prefers_system_expert() -> None:
    employees = sample_employees_as_models()
    assert find_training_plan_preparer_name(employees) == "孙丽"


def test_find_department_head_for_production_operator() -> None:
    employees = sample_employees_as_models()
    head = find_department_head_name("生产部", employees, exclude_name="钱勇")
    assert head == "徐志刚"


def test_resolve_manager_map_fills_training_plan_signatures() -> None:
    employees = sample_employees_as_models()
    resolved = resolve_manager_map({}, employees)
    assert resolved["prepared_by"] == "孙丽"
    assert resolved["reviewed_by"] == "陈建国"
    assert resolved["approved_by"] == "陈建国"


def test_resolve_employee_manager_map_fills_department_head() -> None:
    employees = sample_employees_as_models()
    emp = next(e for e in employees if e.name == "钱勇")
    resolved = resolve_employee_manager_map(emp, {}, employees)
    assert resolved["department_head"] == "徐志刚"
    assert resolved["general_manager"] == "陈建国"


def test_resolve_employee_manager_map_falls_back_to_general_manager() -> None:
    employees = sample_employees_as_models()
    emp = next(e for e in employees if e.name == "张伟")
    resolved = resolve_employee_manager_map(emp, {}, employees)
    assert resolved["department_head"] == "陈建国"
    assert resolved["general_manager"] == "陈建国"


def test_render_list_region_increments_row_index() -> None:
    rows = build_roster_list_data([
        _employee("张三", "生产部"),
        _employee("李四", "品质部"),
        _employee("王五", "综管部"),
    ])["employee_rows"]
    html = render_list_region(
        "<tr><td>{{row.index}}</td><td>{{employee.name}}</td></tr>",
        rows,
    )
    assert "<tr><td>1</td><td>张三</td></tr>" in html
    assert "<tr><td>2</td><td>李四</td></tr>" in html
    assert "<tr><td>3</td><td>王五</td></tr>" in html
    assert "{{row.index}}" not in html


def test_generate_roster_assigns_sequential_row_index() -> None:
    template_base = Path(__file__).parent.parent.parent / "template"
    loader = TemplateLoader(template_base)
    employees = [
        _employee("张三", "生产部"),
        _employee("李四", "品质部"),
    ]
    result = generate_roster(employees, loader, {"name": "示例企业有限公司"})
    assert result.template_id == TMPL_ROSTER
    assert "<td>1</td>" in result.html
    assert "<td>2</td>" in result.html
    assert "{{row.index}}" not in result.html
    assert "张三" in result.html
    assert "李四" in result.html
