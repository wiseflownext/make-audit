"""Signature upload API."""
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response

from app.services.signature import SignatureStore
from app.api import intake as _intake_module
from app.core.http import attachment_disposition

router = APIRouter()

_sig_store = SignatureStore()


@router.get("/employees")
async def list_employees():
    """Return all employee names from the current intake roster."""
    employees = _intake_module._employees
    return {
        "employees": [e["name"] for e in employees],
        "count": len(employees),
    }


@router.post("/upload/{employee_name}")
async def upload_signature(employee_name: str, file: UploadFile = File(...)):
    """Upload a signature photo for *employee_name*.

    When the uploaded file is a transparent PNG from the H5 canvas pad,
    we store it directly without background removal to preserve quality.
    """
    content = await file.read()
    filename = file.filename or ""
    content_type = file.content_type or ""
    try:
        # Canvas-generated PNGs already have transparent backgrounds; skip removal.
        if content_type == "image/png" or filename.endswith(".png"):
            _sig_store.store_raw(employee_name.strip(), content)
        else:
            _sig_store.add(employee_name, content, filename=filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"签名处理失败: {exc}")
    return {"ok": True, "employee": employee_name}


@router.get("/")
async def list_signatures():
    return {"employees_with_signatures": _sig_store.names()}


@router.delete("/{employee_name}")
async def delete_signature(employee_name: str):
    _sig_store.delete(employee_name)
    return {"ok": True}


@router.delete("/")
async def clear_all_signatures():
    """Clear all signatures (admin operation)."""
    _sig_store.clear()
    return {"ok": True, "cleared": True}


@router.get("/export")
async def export_signatures():
    """Export all signatures as a ZIP archive."""
    if not _sig_store.names():
        raise HTTPException(status_code=404, detail="暂无签名数据")
    zip_bytes = _sig_store.export_zip()
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers=attachment_disposition("signatures.zip"),
    )


def get_sig_store() -> SignatureStore:
    return _sig_store
