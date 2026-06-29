"""Unit tests for training record generation."""
from __future__ import annotations

from datetime import date

from app.core.calendar import calendar_for_years
from app.models.sample_roster_data import sample_employees_as_models
from app.services.training_generator import (
    build_sessions,
    load_training_plan,
    parse_training_time_period,
    resolve_trainer_name,
    schedule_date_in_period,
)


def test_parse_training_time_period() -> None:
    start, end = parse_training_time_period("3.2-3.6", 2026)
    assert start == date(2026, 3, 2)
    assert end == date(2026, 3, 6)

    assert parse_training_time_period("入职后第一天", 2026) is None
    assert parse_training_time_period("", 2026) is None


def test_schedule_avoids_new_year_holiday_2026() -> None:
    cal = calendar_for_years([2026])
    assert not cal.is_working_day(date(2026, 1, 1))

    start, end = parse_training_time_period("01.05-01.06", 2026)
    assert start is not None and end is not None
    sched = schedule_date_in_period(start, end, cal)
    assert sched == date(2026, 1, 5)


def test_resolve_trainer_name_uses_roster_not_role_label() -> None:
    employees = sample_employees_as_models()
    course = {"讲师": "综管部主管", "面向对象": "全体员工", "记录讲师": ""}
    assert resolve_trainer_name(course, employees) == "陈建国"

    course = {"讲师": "质量部负责人", "面向对象": "检验员、实验员", "记录讲师": ""}
    assert resolve_trainer_name(course, employees) == "马健"

    course = {"讲师": "质量部负责人", "面向对象": "检验员、实验员", "记录讲师": "孙林宇"}
    assert resolve_trainer_name(course, employees) == "孙林宇"

    course = {"讲师": "车间主任", "面向对象": "操作工", "记录讲师": ""}
    assert resolve_trainer_name(course, employees) in {"胡斌", "朱伟"}


def test_annual_sessions_use_training_time_not_jan_first() -> None:
    employees = sample_employees_as_models()
    plan = load_training_plan()
    cal = calendar_for_years([2026])
    sessions = build_sessions(plan, employees, [2026], cal)
    annual = [s for s in sessions if s.plan_type == "annual"]

    assert annual
    assert all(s.scheduled_date != date(2026, 1, 1) for s in annual)

    first_course = next(s for s in annual if s.course_name == "劳动合同相关内容培训")
    assert first_course.scheduled_date.month == 3
    assert first_course.scheduled_date.day == 2
    assert first_course.trainer == "陈建国"


def test_personal_record_dates_match_annual_sessions() -> None:
    employees = sample_employees_as_models()
    plan = load_training_plan()
    cal = calendar_for_years([2026])
    sessions = build_sessions(plan, employees, [2026], cal)
    annual = [s for s in sessions if s.plan_type == "annual"]
    by_name = {s.course_name: s for s in annual}

    labor_course = by_name["劳动合同相关内容培训"]
    assert labor_course.trainer
    assert "主管" not in labor_course.trainer
    assert "负责人" not in labor_course.trainer
    assert labor_course.scheduled_date == date(2026, 3, 2)


def test_attendance_list_data_fills_all_attendees() -> None:
    from app.services.training_generator import build_attendance_list_data

    employees = sample_employees_as_models()
    plan = load_training_plan()
    cal = calendar_for_years([2026])
    sessions = build_sessions(plan, employees, [2026], cal)
    all_staff = next(s for s in sessions if s.target_audience == "全体员工")

    rows = build_attendance_list_data(all_staff.attendees)["attendance_rows"]
    assert len(all_staff.attendees) > 1
    assert len(rows) >= 14
    assert rows[0]["employee"]["name"] == all_staff.attendees[0].name
    assert rows[1]["employee"]["name"] == all_staff.attendees[1].name
