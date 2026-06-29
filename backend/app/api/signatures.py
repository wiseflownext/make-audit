"""Signature upload API."""
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.services.signature import SignatureStore

router = APIRouter()

_sig_store = SignatureStore()


@router.post("/upload/{employee_name}")
async def upload_signature(employee_name: str, file: UploadFile = File(...)):
    """Upload a signature photo for *employee_name*."""
    content = await file.read()
    try:
        _sig_store.add(employee_name, content, filename=file.filename or "")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"签名处理失败: {exc}")
    return {"ok": True, "employee": employee_name}


@router.get("/")
async def list_signatures():
    return {"employees_with_signatures": _sig_store.names()}


@router.delete("/{employee_name}")
async def delete_signature(employee_name: str):
    _sig_store._store.pop(employee_name, None)
    return {"ok": True}


def get_sig_store() -> SignatureStore:
    return _sig_store
