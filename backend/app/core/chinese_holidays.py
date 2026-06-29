"""Official Chinese public holidays and makeup workdays (2024–2026).

Data sourced from State Council holiday notices (国办发明电).
"""
from __future__ import annotations

from datetime import date

# fmt: off
_HOLIDAY_RANGES: dict[int, list[tuple[int, int, int, int, int, int]]] = {
    2024: [
        (1, 1, 1, 1),             # 元旦
        (2, 10, 2, 17),           # 春节
        (4, 4, 4, 6),             # 清明
        (5, 1, 5, 5),             # 劳动节
        (6, 10, 6, 10),           # 端午
        (9, 15, 9, 17),           # 中秋
        (10, 1, 10, 7),           # 国庆
    ],
    2025: [
        (1, 1, 1, 1),             # 元旦
        (1, 28, 2, 4),            # 春节
        (4, 4, 4, 6),             # 清明
        (5, 1, 5, 5),             # 劳动节
        (5, 31, 6, 2),            # 端午
        (10, 1, 10, 8),           # 国庆+中秋
    ],
    2026: [
        (1, 1, 1, 3),             # 元旦
        (2, 15, 2, 23),           # 春节
        (4, 4, 4, 6),             # 清明
        (5, 1, 5, 5),             # 劳动节
        (6, 19, 6, 21),           # 端午
        (9, 25, 9, 27),           # 中秋
        (10, 1, 10, 7),           # 国庆
    ],
}

_MAKEUP_DAYS: dict[int, list[tuple[int, int, int]]] = {
    2024: [
        (2, 4), (2, 18),          # 春节调休
        (4, 7),                   # 清明调休
        (4, 28), (5, 11),         # 劳动节调休
        (9, 14), (9, 29),         # 中秋/国庆调休
        (10, 12),
    ],
    2025: [
        (1, 26),                  # 春节调休
        (4, 27),                  # 劳动节调休
        (9, 28), (10, 11),        # 国庆调休
    ],
    2026: [
        (1, 4),                   # 元旦调休（周日上班）
        (2, 14), (2, 28),         # 春节调休
        (5, 9),                   # 劳动节调休
        (9, 20), (10, 10),        # 国庆调休
    ],
}
# fmt: on


def _dates_in_range(year: int, sm: int, sd: int, em: int, ed: int) -> list[date]:
    start = date(year, sm, sd)
    end = date(year, em, ed)
    result: list[date] = []
    d = start
    while d <= end:
        result.append(d)
        d = date.fromordinal(d.toordinal() + 1)
    return result


def holidays_for_year(year: int) -> list[date]:
    """Return all public holiday dates for *year*."""
    result: list[date] = []
    for sm, sd, em, ed in _HOLIDAY_RANGES.get(year, []):
        result.extend(_dates_in_range(year, sm, sd, em, ed))
    return result


def makeup_days_for_year(year: int) -> list[date]:
    """Return makeup working days (normally off) for *year*."""
    return [date(year, m, d) for m, d in _MAKEUP_DAYS.get(year, [])]


def holidays_for_years(years: list[int]) -> list[date]:
    seen: set[date] = set()
    result: list[date] = []
    for year in years:
        for d in holidays_for_year(year):
            if d not in seen:
                seen.add(d)
                result.append(d)
    return result


def makeup_days_for_years(years: list[int]) -> list[date]:
    seen: set[date] = set()
    result: list[date] = []
    for year in years:
        for d in makeup_days_for_year(year):
            if d not in seen:
                seen.add(d)
                result.append(d)
    return result
