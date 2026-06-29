"""Parse combined intake workbook (enterprise + roster sheets)."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd

from app.models.employee import Employee, parse_roster
from app.models.enterprise import parse_enterprise
from app.models.enterprise_template import ENTERPRISE_SHEET_TITLE
from app.models.roster_template import ROSTER_SHEET_TITLE

ENTERPRISE_SHEET_ALIASES = frozenset({ENTERPRISE_SHEET_TITLE, "enterprise", "企业资料"})
ROSTER_SHEET_ALIASES = frozenset({ROSTER_SHEET_TITLE, "roster", "花名册"})


class IntakeValidationError(ValueError):
    """Raised when the combined intake file fails validation."""


def _match_sheet(name: str, aliases: frozenset[str]) -> bool:
    cleaned = name.strip()
    lowered = {a.lower() for a in aliases}
    return cleaned in aliases or cleaned.lower() in lowered


def _resolve_sheets(sheet_names: list[str]) -> tuple[str, str]:
    enterprise_sheet = next((n for n in sheet_names if _match_sheet(n, ENTERPRISE_SHEET_ALIASES)), None)
    roster_sheet = next((n for n in sheet_names if _match_sheet(n, ROSTER_SHEET_ALIASES)), None)

    if enterprise_sheet is None:
        enterprise_sheet = sheet_names[0]

    if roster_sheet is None:
        roster_sheet = sheet_names[1] if len(sheet_names) > 1 else sheet_names[0]

    if enterprise_sheet == roster_sheet:
        if len(sheet_names) < 2:
            raise IntakeValidationError(
                f"上传文件需包含「{ENTERPRISE_SHEET_TITLE}」与「{ROSTER_SHEET_TITLE}」两个工作表。"
            )
        roster_sheet = sheet_names[1] if sheet_names[0] == enterprise_sheet else sheet_names[0]

    return enterprise_sheet, roster_sheet


def parse_intake(source: bytes | Path, filename: str = "") -> tuple[dict[str, str], list[Employee]]:
    """Parse a combined Excel file with enterprise and roster sheets."""
    if isinstance(source, Path):
        raw_bytes = source.read_bytes()
        fname = source.name
    else:
        raw_bytes = source
        fname = filename

    ext = Path(fname).suffix.lower() if fname else ""
    if ext == ".csv":
        raise IntakeValidationError(
            "请上传包含多个工作表的 Excel 文件（.xlsx），企业资料与花名册需在同一文件中。"
        )

    try:
        xl = pd.ExcelFile(BytesIO(raw_bytes))
    except Exception as exc:
        raise IntakeValidationError(f"无法读取 Excel 文件: {exc}") from exc

    if len(xl.sheet_names) < 2:
        raise IntakeValidationError(
            f"上传文件需包含「{ENTERPRISE_SHEET_TITLE}」与「{ROSTER_SHEET_TITLE}」两个工作表。"
        )

    enterprise_sheet, roster_sheet = _resolve_sheets(xl.sheet_names)
    enterprise = parse_enterprise(raw_bytes, filename=fname, sheet_name=enterprise_sheet)
    employees = parse_roster(raw_bytes, filename=fname, sheet_name=roster_sheet)
    return enterprise, employees
