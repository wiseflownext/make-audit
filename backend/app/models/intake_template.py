"""Combined Excel template: enterprise info + employee roster in separate sheets."""
from __future__ import annotations

from io import BytesIO

import openpyxl

from app.models.enterprise_template import ENTERPRISE_SHEET_TITLE, write_enterprise_sheet
from app.models.roster_template import ROSTER_SHEET_TITLE, write_roster_sheet

INTAKE_TEMPLATE_FILENAME = "审核资料上传模板.xlsx"


def generate_intake_template() -> bytes:
    """Return a workbook with enterprise and roster sheets."""
    wb = openpyxl.Workbook()
    ws_enterprise = wb.active
    ws_enterprise.title = ENTERPRISE_SHEET_TITLE
    write_enterprise_sheet(ws_enterprise)

    ws_roster = wb.create_sheet(ROSTER_SHEET_TITLE)
    write_roster_sheet(ws_roster)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
