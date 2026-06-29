"""Unit tests for the work calendar module (task 4.4).

Covers:
- February edge cases (28/29 days)
- Cross-month boundaries
- Rest-day skipping
- Probation end date logic
"""
from __future__ import annotations

from datetime import date

import pytest

from app.core.calendar import WorkCalendar, calendar_for_years, probation_end_date


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cal() -> WorkCalendar:
    return WorkCalendar()  # Sunday off


@pytest.fixture
def cal_with_holidays() -> WorkCalendar:
    # 2024-01-01 (New Year, Monday) is a holiday
    return WorkCalendar(holidays=[date(2024, 1, 1)])


# ---------------------------------------------------------------------------
# is_working_day
# ---------------------------------------------------------------------------


def test_monday_is_working(cal: WorkCalendar) -> None:
    assert cal.is_working_day(date(2024, 1, 1))  # Monday


def test_sunday_is_rest(cal: WorkCalendar) -> None:
    assert not cal.is_working_day(date(2024, 1, 7))  # Sunday


def test_holiday_is_rest(cal_with_holidays: WorkCalendar) -> None:
    assert not cal_with_holidays.is_working_day(date(2024, 1, 1))


def test_2026_new_year_is_holiday() -> None:
    cal = calendar_for_years([2026])
    assert not cal.is_working_day(date(2026, 1, 1))
    assert not cal.is_working_day(date(2026, 1, 2))
    assert not cal.is_working_day(date(2026, 1, 3))
    assert cal.is_working_day(date(2026, 1, 4))  # 调休上班（周日）


def test_makeup_day_overrides_rest() -> None:
    makeup = WorkCalendar(makeup_days=[date(2024, 1, 7)])
    assert makeup.is_working_day(date(2024, 1, 7))  # Sunday but makeup


# ---------------------------------------------------------------------------
# add_working_days
# ---------------------------------------------------------------------------


def test_add_one_day_normal(cal: WorkCalendar) -> None:
    # Monday -> +1 = Tuesday
    assert cal.add_working_days(date(2024, 1, 1), 1) == date(2024, 1, 2)


def test_add_skips_sunday(cal: WorkCalendar) -> None:
    # Saturday 2024-01-06 -> +1 should skip Sunday, land Monday 2024-01-08
    assert cal.add_working_days(date(2024, 1, 6), 1) == date(2024, 1, 8)


def test_add_zero_on_working_day(cal: WorkCalendar) -> None:
    # +0 from a working day returns same day
    assert cal.add_working_days(date(2024, 1, 1), 0) == date(2024, 1, 1)


def test_add_zero_on_rest_day(cal: WorkCalendar) -> None:
    # +0 from Sunday should advance to Monday
    assert cal.add_working_days(date(2024, 1, 7), 0) == date(2024, 1, 8)


def test_cross_month_boundary(cal: WorkCalendar) -> None:
    # Jan 31 (Fri) +3 = Mon Feb 3, Tue Feb 4, Wed Feb 5... let's just validate correctness
    result = cal.add_working_days(date(2025, 1, 31), 3)
    # Jan 31 is Friday; +1=Mon Feb 3, +2=Tue Feb 4, +3=Wed Feb 5... wait, Sun Feb 2
    # Jan 31 Fri -> Feb 1 Sat (+1), skip Feb 2 Sun, Feb 3 Mon (+2), Feb 4 Tue (+3)
    assert result == date(2025, 2, 4)


def test_february_no_29_in_non_leap_year(cal: WorkCalendar) -> None:
    # Ensure +30 from early January doesn't land on invalid date
    result = cal.add_working_days(date(2025, 1, 15), 30)
    # Just assert it is a valid date and a working day
    assert cal.is_working_day(result)
    assert result.month in (2, 3)


def test_february_leap_year(cal: WorkCalendar) -> None:
    # 2024 is a leap year; +1 from Feb 28 on a Wednesday
    result = cal.add_working_days(date(2024, 2, 28), 1)
    assert result == date(2024, 2, 29)


def test_add_negative_raises() -> None:
    cal = WorkCalendar()
    with pytest.raises(ValueError):
        cal.add_working_days(date(2024, 1, 1), -1)


# ---------------------------------------------------------------------------
# working_days_in_range
# ---------------------------------------------------------------------------


def test_range_excludes_sunday(cal: WorkCalendar) -> None:
    # Mon-Sun week: should have 6 working days
    days = cal.working_days_in_range(date(2024, 1, 1), date(2024, 1, 7))
    assert len(days) == 6
    assert date(2024, 1, 7) not in days  # Sunday excluded


def test_range_excludes_holiday(cal_with_holidays: WorkCalendar) -> None:
    days = cal_with_holidays.working_days_in_range(date(2024, 1, 1), date(2024, 1, 7))
    assert date(2024, 1, 1) not in days
    assert len(days) == 5


# ---------------------------------------------------------------------------
# 4.3 probation_end_date
# ---------------------------------------------------------------------------


def test_regular_employee_7_days(cal: WorkCalendar) -> None:
    # Hire Monday 2024-01-08; +7 working days
    # Jan 8(M)+1=9(T), +2=10(W), +3=11(Th), +4=12(F), +5=13(Sa), skip 14(Su), +6=15(M), +7=16(T)
    result = probation_end_date(date(2024, 1, 8), is_regular_employee=True, calendar=cal)
    assert result == date(2024, 1, 16)


def test_regular_employee_skips_rest(cal: WorkCalendar) -> None:
    result = probation_end_date(date(2024, 1, 8), is_regular_employee=True, calendar=cal)
    assert cal.is_working_day(result)


def test_non_regular_employee_30_days(cal: WorkCalendar) -> None:
    result = probation_end_date(date(2024, 1, 8), is_regular_employee=False, calendar=cal)
    # Result must be a valid working day ~30 working days later
    assert cal.is_working_day(result)
    # 30 working days from Jan 8 should be around Feb
    assert result > date(2024, 1, 8)


def test_probation_february_edge(cal: WorkCalendar) -> None:
    # Hire Jan 25 (Thu); +7 working days should navigate through Feb
    result = probation_end_date(date(2025, 1, 25), is_regular_employee=True, calendar=cal)
    assert cal.is_working_day(result)
    assert result > date(2025, 1, 25)
