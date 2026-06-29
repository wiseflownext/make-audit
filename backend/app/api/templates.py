"""Template management API: list, get HTML, save, validate, preview."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any

from app.core.validator import validate_templates
from app.templates.loader import TemplateLoader
from app.templates.placeholder import PlaceholderParser

router = APIRouter()

TEMPLATE_BASE = Path(__file__).parent.parent.parent.parent / "template"
_loader = TemplateLoader(TEMPLATE_BASE)
_parser = PlaceholderParser()


def _fresh_loader() -> TemplateLoader:
    _loader.reload()
    return _loader


@router.get("/")
async def list_templates(category: str | None = None):
    templates = _fresh_loader().list_templates(category)
    return [
        {
            "id": t.id,
            "title": t.title,
            "category": t.category,
            "generation_granularity": t.generation_granularity,
            "status": t.status,
            "output_naming": t.output_naming,
        }
        for t in templates
    ]


@router.get("/categories")
async def list_categories():
    return _fresh_loader().list_categories()


@router.get("/{template_id}/html")
async def get_template_html(template_id: str):
    tmpl = _fresh_loader().get_by_id(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    html = tmpl.template_html_path.read_text(encoding="utf-8")
    return {"id": template_id, "html": html}


class SaveHtmlBody(BaseModel):
    html: str


@router.put("/{template_id}/html")
async def save_template_html(template_id: str, body: SaveHtmlBody):
    tmpl = _fresh_loader().get_by_id(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    # Validate placeholders before saving
    malformed = _parser.detect_malformed(body.html)
    if malformed:
        raise HTTPException(
            status_code=422,
            detail=f"HTML 包含格式错误的占位符: {malformed[:5]}",
        )
    tmpl.template_html_path.write_text(body.html, encoding="utf-8")
    return {"ok": True}


@router.get("/{template_id}/placeholders")
async def get_placeholders(template_id: str):
    tmpl = _fresh_loader().get_by_id(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    html = tmpl.template_html_path.read_text(encoding="utf-8")
    placeholders = _parser.extract(html)
    malformed = _parser.detect_malformed(html)
    return {
        "placeholders": [{"namespace": p.namespace, "key": p.key} for p in placeholders],
        "malformed": malformed,
    }


@router.get("/{template_id}/preview", response_class=HTMLResponse)
async def preview_template(template_id: str):
    """Render template with sample data for preview."""
    from app.services.renderer import preview_html
    from app.services.sample_context import build_sample_context, build_sample_list_data

    tmpl = _fresh_loader().get_by_id(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    html = preview_html(
        tmpl,
        build_sample_context(),
        build_sample_list_data(template_id),
    )
    return html


@router.get("/validate/all")
async def validate_all_templates():
    """Run gap validation on all templates and return report."""
    report = validate_templates(TEMPLATE_BASE)
    return {
        "templates_scanned": report.templates_scanned,
        "templates_with_issues": report.templates_with_issues,
        "gaps": [
            {
                "template_id": g.template_id,
                "template_title": g.template_title,
                "unknown_namespaces": [str(p) for p in g.unknown_namespaces],
                "unknown_keys": [str(p) for p in g.unknown_keys],
                "malformed": g.malformed,
            }
            for g in report.gaps
            if g.has_issues
        ],
    }
