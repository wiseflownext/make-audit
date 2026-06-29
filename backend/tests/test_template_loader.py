"""Tests for the template loader (Task 2.1)."""
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.templates.loader import TemplateLoader, TemplateMeta  # noqa: E402

TEMPLATE_BASE = (
    Path(__file__).parent.parent.parent / "template"
)


def test_loader_finds_all_hr_templates():
    loader = TemplateLoader(TEMPLATE_BASE)
    templates = loader.list_templates(category="人力资源")
    assert len(templates) >= 10, f"Expected ≥10 HR templates, got {len(templates)}"


def test_loader_returns_template_meta_objects():
    loader = TemplateLoader(TEMPLATE_BASE)
    templates = loader.list_templates(category="人力资源")
    for t in templates:
        assert isinstance(t, TemplateMeta)


def test_meta_required_fields_present():
    loader = TemplateLoader(TEMPLATE_BASE)
    templates = loader.list_templates(category="人力资源")
    for t in templates:
        assert t.id, f"Missing id in template at {t.path}"
        assert t.title, f"Missing title in {t.id}"
        assert t.generation_granularity, f"Missing generation_granularity in {t.id}"
        assert t.template_html_path.exists(), (
            f"template.html not found for {t.id}: {t.template_html_path}"
        )


def test_loader_get_by_id():
    loader = TemplateLoader(TEMPLATE_BASE)
    templates = loader.list_templates(category="人力资源")
    first = templates[0]
    fetched = loader.get_by_id(first.id)
    assert fetched is not None
    assert fetched.id == first.id


def test_loader_get_nonexistent_id_returns_none():
    loader = TemplateLoader(TEMPLATE_BASE)
    assert loader.get_by_id("nonexistent-id-xyz") is None


def test_loader_categories():
    loader = TemplateLoader(TEMPLATE_BASE)
    cats = loader.list_categories()
    assert "人力资源" in cats


def test_template_html_readable():
    loader = TemplateLoader(TEMPLATE_BASE)
    templates = loader.list_templates(category="人力资源")
    for t in templates:
        content = t.template_html_path.read_text(encoding="utf-8")
        assert len(content) > 0, f"Empty template.html for {t.id}"
