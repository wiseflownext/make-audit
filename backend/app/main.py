"""FastAPI application entry point."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import intake, generate, templates, signatures

app = FastAPI(
    title="HR Audit Document Generator",
    description="自动生成人力资源审核资料包的 Web 服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake.router, prefix="/api/intake", tags=["intake"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(signatures.router, prefix="/api/signatures", tags=["signatures"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
