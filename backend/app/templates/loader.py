"""Template loader: discovers and indexes meta.yaml + template.html assets."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TemplateMeta:
    id: str
    title: str
    generation_granularity: str
    status: str
    data_sources: list[str]
    variables: list[dict[str, Any]]
    output_naming: str
    precheck_enabled: bool
    signature_mappings: list[dict[str, Any]]
    date_mappings: list[dict[str, Any]]
    checkbox_mappings: list[dict[str, Any]]
    render_mode: str
    category: str
    path: Path
    template_html_path: Path
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(
        cls, yaml_path: Path, category: str, template_base: Path
    ) -> "TemplateMeta":
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        html_path = yaml_path.parent / "template.html"
        return cls(
            id=data.get("id", ""),
            title=yaml_path.parent.name,
            generation_granularity=data.get("generation_granularity", ""),
            status=data.get("status", "unknown"),
            data_sources=data.get("data_sources", []),
            variables=data.get("variables") or [],
            output_naming=data.get("output_naming", ""),
            precheck_enabled=bool(data.get("precheck_enabled", True)),
            signature_mappings=data.get("signature_mappings") or [],
            date_mappings=data.get("date_mappings") or [],
            checkbox_mappings=data.get("checkbox_mappings") or [],
            render_mode=data.get("render_mode", "a4-print"),
            category=category,
            path=yaml_path,
            template_html_path=html_path,
            raw=data,
        )


class TemplateLoader:
    """Discovers all ``meta.yaml`` + ``template.html`` pairs under *base_dir*
    and provides lookup by category or ID.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base = base_dir
        self._templates: dict[str, TemplateMeta] = {}
        self._by_category: dict[str, list[TemplateMeta]] = {}
        self._load_all()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_categories(self) -> list[str]:
        return sorted(self._by_category.keys())

    def list_templates(self, category: str | None = None) -> list[TemplateMeta]:
        if category is None:
            return list(self._templates.values())
        return list(self._by_category.get(category, []))

    def get_by_id(self, template_id: str) -> TemplateMeta | None:
        return self._templates.get(template_id)

    def reload(self) -> None:
        """Re-scan template directory (meta.yaml changes live outside backend reload)."""
        self._templates.clear()
        self._by_category.clear()
        self._load_all()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        for meta_path in sorted(self._base.rglob("meta.yaml")):
            # Category is the top-level folder directly under base_dir
            rel = meta_path.relative_to(self._base)
            category = rel.parts[0]
            try:
                tmpl = TemplateMeta.from_yaml(meta_path, category, self._base)
            except Exception:
                continue
            if not tmpl.id:
                continue
            self._templates[tmpl.id] = tmpl
            self._by_category.setdefault(category, []).append(tmpl)
