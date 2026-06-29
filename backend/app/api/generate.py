"""Document generation API: trigger generation and download ZIP."""
from __future__ import annotations

import asyncio
import io
import json
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel

from app.api import intake as intake_state
from app.core.http import attachment_disposition
from app.api.signatures import get_sig_store
from app.core.calendar import WorkCalendar, calendar_for_years
from app.models.employee import Employee, _parse_date_cell
from app.services.hr_generator import (
    DocGenResult,
    generate_all_hr_docs,
    generate_roster,
    generate_satisfaction_analysis_reports,
    generate_satisfaction_surveys,
)
from app.services.package_export import (
    PackageManifest,
    EmptyPackageError,
    assert_non_empty,
    build_manifest,
    pack_to_zip,
)
from app.services.incentive_generator import generate_incentive_forms
from app.services.training_generator import (
    build_sessions,
    generate_annual_training_plans,
    generate_attendance_records,
    generate_personal_training_records,
    load_training_plan,
)
from app.services.renderer import html_contents_to_pdf, html_to_pdf
from app.templates.loader import TemplateLoader

router = APIRouter()


# ---------------------------------------------------------------------------
# Download progress tracking
# ---------------------------------------------------------------------------

@dataclass
class _DownloadProgress:
    total: int = 0
    done: int = 0
    current: str = ""
    started: bool = False
    finished: bool = False
    error: str = ""
    started_at: float = field(default_factory=time.time)


_download_progress = _DownloadProgress()


def _content_cache_key(r: "DocGenResult") -> tuple[str, str]:
    """Stable cache key — never use ``id(r)`` (Python reuses object ids after GC)."""
    return (r.template_id, r.output_filename)


def _to_content_bytes(
    r: "DocGenResult",
    cache: dict[tuple[str, str], bytes] | None = None,
) -> bytes:
    """Return renderable bytes for ZIP storage (HTML during generate; PDF at download)."""
    if cache is not None:
        key = _content_cache_key(r)
        if key in cache:
            return cache[key]
    if r.pdf_bytes:
        out = r.pdf_bytes
    elif r.html:
        out = r.html.encode("utf-8")
    else:
        out = b""
    if cache is not None:
        cache[_content_cache_key(r)] = out
    return out


def _content_to_pdf(content: bytes) -> bytes:
    """Convert stored HTML bytes to PDF; pass through existing PDF bytes."""
    if content.startswith(b"%PDF"):
        return content
    stripped = content.lstrip()
    if stripped.startswith(b"<") or stripped.startswith(b"<!"):
        try:
            pdf = html_to_pdf(content.decode("utf-8"))
            if pdf:
                return pdf
        except Exception:
            pass
    return content


def _build_zip_with_pdf(manifest: PackageManifest, content_map: dict[str, bytes]) -> bytes:
    """Build ZIP, converting unique HTML entries to PDF one at a time, tracking progress."""
    global _download_progress

    paths: list[str] = []
    for entry in manifest.entries:
        if entry.skipped:
            continue
        if entry.filename in content_map and entry.filename not in paths:
            paths.append(entry.filename)

    _download_progress.total = len(paths)
    _download_progress.done = 0
    _download_progress.started = True
    _download_progress.finished = False
    _download_progress.error = ""

    pdf_map: dict[str, bytes] = {}
    for path in paths:
        _download_progress.current = Path(path).name
        content = content_map[path]
        # Convert single file via batch helper (reuses one browser session)
        results = html_contents_to_pdf([content])
        pdf_map[path] = results[0]
        _download_progress.done += 1

    pairs: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for entry in manifest.entries:
        if entry.skipped or entry.filename in seen:
            continue
        content = pdf_map.get(entry.filename)
        if content is None:
            continue
        seen.add(entry.filename)
        pairs.append((entry.filename, content))

    zip_bytes = pack_to_zip(pairs)
    _download_progress.finished = True
    _download_progress.current = ""
    return zip_bytes


TEMPLATE_BASE = Path(__file__).parent.parent.parent.parent / "template"
_loader = TemplateLoader(TEMPLATE_BASE)

# Cached generate result
_last_manifest: PackageManifest | None = None
_last_content_map: dict[str, bytes] = {}
_last_precheck: list[dict] = []


def _employee_from_dict(d: dict) -> Employee:
    hire = _parse_date_cell(d.get("hire_date"))
    if hire is None:
        hire = date.today()
    birth_raw = d.get("birth_date")
    birth = _parse_date_cell(birth_raw) if birth_raw else None
    return Employee(
        name=d.get("name", ""),
        department_name=d.get("department_name", ""),
        position_name=d.get("position_name", ""),
        hire_date=hire,
        birth_date=birth,
        gender=d.get("gender", ""),
        id_no=d.get("id_no", ""),
        phone=d.get("phone", ""),
        education=d.get("education", ""),
        school=d.get("school", ""),
        address=d.get("address", ""),
        remark=d.get("remark", ""),
        employment_status=d.get("employment_status", "在职"),
        is_key_position=bool(d.get("is_key_position", False)),
        is_internal_auditor=bool(d.get("is_internal_auditor", False)),
        is_regular_employee=bool(d.get("is_regular_employee", True)),
        is_manager=bool(d.get("is_manager", False)),
    )


class GenerateRequest(BaseModel):
    years: list[int] = []
    manager_map: dict[str, str] = {}


@router.post("/")
async def trigger_generation(req: GenerateRequest):
    """Trigger document generation for all uploaded employees."""
    if not intake_state._enterprise.get("name"):
        raise HTTPException(status_code=422, detail="请先上传企业基础资料（企业名称）")
    if not intake_state._employees:
        raise HTTPException(status_code=422, detail="请先上传员工花名册")

    return await asyncio.to_thread(_run_generation, req)


def _run_generation(req: GenerateRequest) -> dict[str, Any]:
    """Synchronous generation body — runs off the event loop in a worker thread."""
    global _last_manifest, _last_content_map, _last_precheck

    current_year = date.today().year
    years = req.years or [current_year - 2, current_year - 1, current_year]

    employees = [_employee_from_dict(d) for d in intake_state._employees]
    sig_store = get_sig_store()
    enterprise = dict(intake_state._enterprise)

    try:
        training_plan = load_training_plan()
    except Exception:
        training_plan = {"annual_training_plan": {"trainings": []}, "new_employee_training": {"trainings": []}}

    calendar = calendar_for_years(years)
    sessions = build_sessions(training_plan, employees, years, calendar)
    annual_plan_results = generate_annual_training_plans(
        sessions, years, _loader, enterprise, sig_store, employees, req.manager_map or None
    )
    attendance_results = generate_attendance_records(sessions, _loader, enterprise, sig_store)
    personal_training_results = generate_personal_training_records(
        sessions, employees, years, _loader, enterprise, sig_store
    )

    incentive_results = generate_incentive_forms(
        employees, _loader, enterprise, sig_store
    )

    roster_result = generate_roster(employees, _loader, enterprise)

    satisfaction_results = generate_satisfaction_surveys(
        employees, years, _loader, enterprise, sig_store
    )
    satisfaction_report_results = generate_satisfaction_analysis_reports(
        years, _loader, enterprise, sig_store, employees
    )

    all_entries: list[dict] = []
    content_map: dict[str, bytes] = {}
    pdf_cache: dict[tuple[str, str], bytes] = {}

    if roster_result.output_filename:
        roster_path = f"公司级文件/员工档案/{roster_result.output_filename}"
        content_map[roster_path] = _to_content_bytes(roster_result, pdf_cache)
    all_entries.append({
        "filename": f"公司级文件/员工档案/{roster_result.output_filename}" if roster_result.output_filename else "",
        "category": "员工档案",
        "skipped": roster_result.skipped,
        "missing_keys": roster_result.missing_keys,
    })

    for r in annual_plan_results:
        if r.output_filename:
            plan_path = f"公司级文件/年度培训计划/{r.output_filename}"
            content_map[plan_path] = _to_content_bytes(r, pdf_cache)
        all_entries.append({
            "filename": f"公司级文件/年度培训计划/{r.output_filename}" if r.output_filename else "",
            "category": "年度培训计划",
            "skipped": r.skipped,
            "missing_keys": r.missing_keys,
        })

    for r in incentive_results + satisfaction_report_results:
        if r.output_filename:
            path = r.output_filename
            if "分析报告" in r.output_filename:
                path = f"公司级文件/20员工激励/{r.output_filename}"
            content_map[path] = _to_content_bytes(r, pdf_cache)
        all_entries.append({
            "filename": (
                f"公司级文件/20员工激励/{r.output_filename}"
                if r.output_filename and "分析报告" in r.output_filename
                else r.output_filename
            ),
            "category": "员工激励" if "分析报告" not in (r.output_filename or "") else "满意度分析",
            "skipped": r.skipped,
            "missing_keys": r.missing_keys,
        })

    for r in satisfaction_results:
        if r.output_filename:
            content_map[r.output_filename] = _to_content_bytes(r, pdf_cache)

    # Add attendance records to content_map at company level (deduplicated).
    # They are session-level documents shared across all employees.
    for r in attendance_results:
        if r.output_filename:
            att_path = f"公司级文件/培训签到记录/{r.output_filename}"
            content_map[att_path] = _to_content_bytes(r, pdf_cache)
        all_entries.append({
            "filename": f"公司级文件/培训签到记录/{r.output_filename}" if r.output_filename else "",
            "category": "培训签到记录",
            "skipped": r.skipped,
            "missing_keys": r.missing_keys,
        })

    for emp in employees:
        hr_results = generate_all_hr_docs(
            emp,
            _loader,
            enterprise,
            sig_store,
            years,
            calendar,
            req.manager_map or None,
            employees,
        )
        onboarding = [r for r in hr_results if any(
            t in r.template_id for t in ["2新员工入职需知", "3公司入职人员登记表", "4用工合同协议书"]
        )]
        probation = [r for r in hr_results if any(
            t in r.template_id for t in ["5新员工入职岗位培训评价表", "6转正申请表", "7技能履历个人管理表"]
        )]
        satisfaction = [
            r for r in satisfaction_results
            if emp.name in r.output_filename
        ]

        emp_personal = [r for r in personal_training_results if emp.name in r.output_filename]

        manifest = build_manifest(
            emp.name,
            onboarding,
            probation,
            satisfaction,
            [],  # attendance records are handled at company level
            emp_personal,
        )

        for entry in manifest.entries:
            # For HTML content, encode to bytes
            # Find matching result
            matched = False
            for res_list in [
                hr_results,
                personal_training_results,
                incentive_results,
                satisfaction_results,
                [roster_result],
            ]:
                if matched:
                    break
                for r in res_list:
                    if not r.output_filename:
                        continue
                    if entry.filename.endswith(r.output_filename):
                        content_map[entry.filename] = _to_content_bytes(r, pdf_cache)
                        matched = True
                        break
            all_entries.append({
                "filename": entry.filename,
                "category": entry.category,
                "skipped": entry.skipped,
                "missing_keys": entry.missing_keys,
            })

    _last_content_map = content_map
    _last_manifest = PackageManifest(
        entries=[e for e in [
            type("E", (), {
                "filename": x["filename"],
                "category": x["category"],
                "template_id": "",
                "missing_keys": x["missing_keys"],
                "skipped": x["skipped"],
                "skip_reason": "",
            })()
            for x in all_entries
        ]]
    )
    _last_precheck = [e for e in all_entries if e["missing_keys"] or e["skipped"]]

    return {
        "ok": True,
        "total": len(all_entries),
        "generated": sum(1 for e in all_entries if not e["skipped"]),
        "precheck_warnings": _last_precheck,
        "manifest": all_entries,
    }


def _require_content_map() -> dict[str, bytes]:
    if _last_manifest is None or not _last_content_map:
        raise HTTPException(status_code=404, detail="尚未生成资料包，请先触发生成。")
    return _last_content_map


def _resolve_file_content(filename: str) -> bytes:
    content_map = _require_content_map()
    if filename not in content_map:
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    return content_map[filename]


def _list_preview_files() -> list[dict[str, str]]:
    content_map = _require_content_map()
    files: list[dict[str, str]] = []
    seen: set[str] = set()
    assert _last_manifest is not None
    for entry in _last_manifest.entries:
        if entry.skipped or not entry.filename or entry.filename in seen:
            continue
        if entry.filename not in content_map:
            continue
        seen.add(entry.filename)
        files.append(
            {
                "filename": entry.filename,
                "category": entry.category,
                "display_name": Path(entry.filename).name,
            }
        )
    return files


def _merge_pdfs(pdf_parts: list[bytes]) -> bytes:
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for part in pdf_parts:
        if not part.startswith(b"%PDF"):
            continue
        reader = PdfReader(io.BytesIO(part))
        for page in reader.pages:
            writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class PrintRequest(BaseModel):
    filenames: list[str]


@router.get("/files")
async def list_files():
    """List generated documents available for preview and printing."""
    files = await asyncio.to_thread(_list_preview_files)
    return {"files": files, "total": len(files)}


@router.get("/preview/{file_path:path}")
async def preview_document(file_path: str):
    """Serve HTML preview inline (for gallery iframe)."""
    content = await asyncio.to_thread(_resolve_file_content, file_path)
    if content.startswith(b"%PDF"):
        return Response(content=content, media_type="application/pdf")
    try:
        html = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="无法预览该文件格式") from exc
    return HTMLResponse(content=html, headers={"Cache-Control": "no-cache"})


@router.get("/pdf/{file_path:path}")
async def get_single_pdf(file_path: str):
    """Convert one document to PDF on demand."""
    content = await asyncio.to_thread(_resolve_file_content, file_path)
    pdf_bytes = await asyncio.to_thread(_content_to_pdf, content)
    name = Path(file_path).name
    if not name.lower().endswith(".pdf"):
        name = Path(name).stem + ".pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=attachment_disposition(name) | {"Cache-Control": "no-cache"},
    )


@router.post("/print")
async def print_documents(req: PrintRequest):
    """Merge selected documents into one PDF for browser printing."""
    if not req.filenames:
        raise HTTPException(status_code=400, detail="请选择至少一份文件")

    content_map = _require_content_map()
    ordered = [f for f in req.filenames if f in content_map]
    if not ordered:
        raise HTTPException(status_code=404, detail="所选文件均不可用")

    def _build_merged() -> bytes:
        pdfs = html_contents_to_pdf([content_map[filename] for filename in ordered])
        merged = _merge_pdfs(pdfs)
        if not merged:
            raise HTTPException(status_code=422, detail="无法生成可打印的 PDF")
        return merged

    pdf_bytes = await asyncio.to_thread(_build_merged)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="print.pdf"', "Cache-Control": "no-cache"},
    )


@router.get("/manifest")
async def get_manifest():
    if _last_manifest is None:
        return {"generated": False, "manifest": []}
    return {
        "generated": True,
        "summary": _last_manifest.summary(),
        "manifest": [
            {"filename": e.filename, "category": e.category, "skipped": e.skipped}
            for e in _last_manifest.entries
        ],
    }


@router.get("/download-progress")
async def download_progress_sse():
    """SSE endpoint: stream download/conversion progress every 500ms."""

    async def event_generator():
        while True:
            p = _download_progress
            data = json.dumps({
                "done": p.done,
                "total": p.total,
                "current": p.current,
                "started": p.started,
                "finished": p.finished,
                "error": p.error,
            }, ensure_ascii=False)
            yield f"data: {data}\n\n"
            if p.finished or p.error:
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/download")
async def download_zip():
    """Download the generated audit package as a ZIP file."""
    global _download_progress
    if _last_manifest is None or not _last_content_map:
        raise HTTPException(status_code=404, detail="尚未生成资料包，请先触发生成。")
    try:
        assert_non_empty(_last_manifest)
    except EmptyPackageError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    _download_progress = _DownloadProgress()
    try:
        zip_bytes = await asyncio.to_thread(_build_zip_with_pdf, _last_manifest, _last_content_map)
    except Exception as exc:
        _download_progress.error = str(exc)
        raise HTTPException(status_code=500, detail=f"打包失败: {exc}")
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers=attachment_disposition("HR审核资料包.zip"),
    )


@router.get("/precheck")
async def get_precheck():
    return {"warnings": _last_precheck}
