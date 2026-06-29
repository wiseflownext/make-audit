"""Work calendar module for computing valid working dates.

Tasks 4.1 – 4.4:
  4.1  Single-day-off (Sunday) calendar with configurable public holidays
  4.2  Compute the N-th working day from a start date
  4.3  Probation end date calculation (regular employees +7 days, others +30 days)
  4.4  (Tests live in tests/test_calendar.py)
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable


# ---------------------------------------------------------------------------
# 4.1 Work Calendar
# ---------------------------------------------------------------------------


class WorkCalendar:
    """Single-rest-day calendar (Sunday off by default).

    Public holidays can be supplied as an iterable of ``date`` objects.
    Makeup workdays (normally off but scheduled as working) can also be added.

    Args:
        rest_weekday: ISO weekday of the weekly rest day (7 = Sunday, 6 = Saturday).
        holidays:     Additional non-working dates (public holidays, etc.).
        makeup_days:  Dates that are normally off but scheduled as working.
    """

    def __init__(
        self,
        rest_weekday: int = 7,
        holidays: Iterable[date] | None = None,
        makeup_days: Iterable[date] | None = None,
    ) -> None:
        self._rest_weekday = rest_weekday
        self._holidays: frozenset[date] = frozenset(holidays or [])
        self._makeup_days: frozenset[date] = frozenset(makeup_days or [])

    def is_working_day(self, d: date) -> bool:
        """Return True when *d* is a working day."""
        if d in self._makeup_days:
            return True
        if d in self._holidays:
            return False
        return d.isoweekday() != self._rest_weekday

    # ---------------------------------------------------------------------------
    # 4.2  Compute N-th working day offset
    # ---------------------------------------------------------------------------

    def add_working_days(self, start: date, days: int) -> date:
        """Return the date that is *days* working days after *start*.

        *start* itself is NOT counted.  If *days* is 0, the first working day
        on or after *start* is returned.

        Examples::

            cal = WorkCalendar()
            # A Monday: +1 → Tuesday
            cal.add_working_days(date(2024, 1, 1), 1)  # → 2024-01-02
        """
        if days < 0:
            raise ValueError("days must be non-negative")

        current = start
        counted = 0
        while counted < days:
            current += timedelta(days=1)
            if self.is_working_day(current):
                counted += 1

        # If days == 0 but start itself is not a working day, advance to next
        if days == 0 and not self.is_working_day(current):
            return self.next_working_day(current)

        return current

    def next_working_day(self, d: date) -> date:
        """Return *d* if it is a working day, otherwise the next working day."""
        while not self.is_working_day(d):
            d += timedelta(days=1)
        return d

    def working_days_in_range(self, start: date, end: date) -> list[date]:
        """Return all working days in [*start*, *end*] inclusive."""
        result: list[date] = []
        d = start
        while d <= end:
            if self.is_working_day(d):
                result.append(d)
            d += timedelta(days=1)
        return result


# ---------------------------------------------------------------------------
# 4.3  Probation end date
# ---------------------------------------------------------------------------

def calendar_for_years(years: list[int] | None = None) -> WorkCalendar:
    """Build a :class:`WorkCalendar` with official holidays for *years*."""
    if not years:
        return WorkCalendar()
    from app.core.chinese_holidays import holidays_for_years, makeup_days_for_years

    return WorkCalendar(
        holidays=holidays_for_years(years),
        makeup_days=makeup_days_for_years(years),
    )


_DEFAULT_CALENDAR = WorkCalendar()


def probation_end_date(
    hire_date: date,
    is_regular_employee: bool,
    calendar: WorkCalendar | None = None,
) -> date:
    """Calculate the probation end (转正) date.

    Regular employees (普通员工) have a 7-working-day probation;
    all others have a 30-working-day probation.

    The result is always a valid working day per the given *calendar*.
    """
    cal = calendar or _DEFAULT_CALENDAR
    offset = 7 if is_regular_employee else 30
    return cal.add_working_days(hire_date, offset)
