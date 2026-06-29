"""Client data intake API: enterprise info, roster upload, template download."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from typing import Any

from app.core.http import attachment_disposition
from app.models.employee import RosterValidationError
from app.models.enterprise import EnterpriseValidationError
from app.models.intake_parser import IntakeValidationError, parse_intake
from app.models.intake_template import INTAKE_TEMPLATE_FILENAME, generate_intake_template

router = APIRouter()

# In-memory session state (single-user audit workstation)
_enterprise: dict[str, Any] = {}
_employees: list[dict] = []


def _employees_to_dicts(employees) -> list[dict]:
    return [
        {
            "name": e.name,
            "department_name": e.department_name,
            "position_name": e.position_name,
            "hire_date": e.hire_date.isoformat(),
            "gender": e.gender,
            "id_no": e.id_no,
            "birth_date": e.birth_date.isoformat() if e.birth_date else "",
            "phone": e.phone,
            "education": e.education,
            "school": e.school,
            "address": e.address,
            "remark": e.remark,
            "employment_status": e.employment_status,
            "is_key_position": e.is_key_position,
            "is_internal_auditor": e.is_internal_auditor,
            "is_regular_employee": e.is_regular_employee,
            "is_manager": e.is_manager,
        }
        for e in employees
    ]


@router.get("/enterprise")
async def get_enterprise():
    return _enterprise


@router.get("/roster")
async def get_roster():
    return {"count": len(_employees), "employees": _employees}


@router.get("/template")
async def download_intake_template():
    """Download combined Excel template (enterprise + roster sheets)."""
    xlsx_bytes = generate_intake_template()
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=attachment_disposition(INTAKE_TEMPLATE_FILENAME),
    )


@router.post("/upload")
async def upload_intake(file: UploadFile = File(...)):
    """Upload combined Excel with enterprise info and employee roster sheets."""
    content = await file.read()
    try:
        enterprise, employees = parse_intake(content, filename=file.filename or "")
    except (IntakeValidationError, EnterpriseValidationError, RosterValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"解析失败: {exc}")

    # Mutate in place so other modules that imported these objects see updates.
    _enterprise.clear()
    _enterprise.update(enterprise)
    _employees.clear()
    _employees.extend(_employees_to_dicts(employees))
    return {
        "ok": True,
        "enterprise": _enterprise,
        "count": len(_employees),
        "employees": _employees,
    }
