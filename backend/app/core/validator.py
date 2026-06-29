"""Validate that all built-in template placeholders resolve against the
canonical namespace registry.  Returns a structured gap report.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.core.namespaces import KNOWN_NAMESPACES, NAMESPACE_KEYS
from app.templates.loader import TemplateLoader
from app.templates.placeholder import Placeholder, PlaceholderParser


@dataclass
class TemplateGap:
    template_id: str
    template_title: str
    unknown_namespaces: list[Placeholder] = field(default_factory=list)
    unknown_keys: list[Placeholder] = field(default_factory=list)
    malformed: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.unknown_namespaces or self.unknown_keys or self.malformed)


@dataclass
class GapReport:
    templates_scanned: int = 0
    templates_with_issues: int = 0
    gaps: list[TemplateGap] = field(default_factory=list)

    def summary_text(self) -> str:
        lines = [
            f"Scanned {self.templates_scanned} templates, "
            f"{self.templates_with_issues} have issues."
        ]
        for gap in self.gaps:
            if not gap.has_issues:
                continue
            lines.append(f"\n[{gap.template_id}] {gap.template_title}")
            for p in gap.unknown_namespaces:
                lines.append(f"  UNKNOWN_NS  {p}")
            for p in gap.unknown_keys:
                lines.append(f"  UNKNOWN_KEY {p}")
            for m in gap.malformed:
                lines.append(f"  MALFORMED   {m}")
        return "\n".join(lines)


def validate_templates(template_base: Path) -> GapReport:
    """Scan all templates under *template_base* and return a gap report."""
    loader = TemplateLoader(template_base)
    parser = PlaceholderParser()
    report = GapReport()

    for tmpl in loader.list_templates():
        report.templates_scanned += 1
        gap = TemplateGap(template_id=tmpl.id, template_title=tmpl.title)

        if not tmpl.template_html_path.exists():
            gap.malformed.append("template.html missing")
            report.gaps.append(gap)
            report.templates_with_issues += 1
            continue

        html = tmpl.template_html_path.read_text(encoding="utf-8")
        gap.malformed = parser.detect_malformed(html)

        for p in parser.extract(html):
            if p.namespace not in KNOWN_NAMESPACES:
                gap.unknown_namespaces.append(p)
            else:
                ns_keys = NAMESPACE_KEYS.get(p.namespace, frozenset())
                # Check whether the key (or a prefix of it) is registered
                full_key = p.full_key  # e.g. "training.exam.score"
                key_part = p.key       # everything after namespace
                matched = key_part in ns_keys or any(
                    key_part == k or key_part.startswith(k + ".") or k.startswith(key_part + ".")
                    for k in ns_keys
                )
                if not matched:
                    gap.unknown_keys.append(p)

        if gap.has_issues:
            report.templates_with_issues += 1
            report.gaps.append(gap)

    return report
