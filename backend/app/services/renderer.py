"""Template rendering engine.

Tasks 6.1 – 6.5:
  6.1  Text / date / checkbox / signature placeholder rendering
  6.2  List-region loop rendering (roster rows, attendance rows, training rows)
  6.3  HTML → PDF output with CJK font & print CSS fixups
  6.4  Output filename generation from ``output_naming`` template
  6.5  Single-template real-data preview (HTML string)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.templates.loader import TemplateMeta
from app.templates.placeholder import PlaceholderParser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

ContextMap = dict[str, dict[str, Any]]
"""Two-level dict:  namespace -> {key -> value}"""

_parser = PlaceholderParser()

# ---------------------------------------------------------------------------
# 6.1  Single-value placeholder rendering
# ---------------------------------------------------------------------------

# Match {{namespace.key}} – may not contain whitespace
_PH_RE = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z0-9_.]+)\}\}")


def _resolve(namespace: str, key: str, context: ContextMap) -> str | None:
    ns_data = context.get(namespace)
    if ns_data is None:
        return None
    # Support dotted sub-keys: training.exam.score → key="exam.score"
    parts = key.split(".")
    node: Any = ns_data
    for part in parts:
        if isinstance(node, dict):
            node = node.get(part)
        else:
            return None
        if node is None:
            return None
    if isinstance(node, bool):
        return "是" if node else "否"
    return str(node)


def render_placeholders(html: str, context: ContextMap) -> tuple[str, list[str]]:
    """Replace all ``{{namespace.key}}`` tokens in *html*.

    Returns ``(rendered_html, missing_keys)`` where *missing_keys* lists any
    tokens that could not be resolved from *context*.
    """
    missing: list[str] = []

    def replacer(m: re.Match) -> str:  # type: ignore[type-arg]
        ns, key = m.group(1), m.group(2)
        value = _resolve(ns, key, context)
        if value is None:
            missing.append(f"{ns}.{key}")
            return m.group(0)  # leave original if missing
        return value

    rendered = _PH_RE.sub(replacer, html)
    return rendered, missing


# ---------------------------------------------------------------------------
# 6.2  List-region loop rendering
# ---------------------------------------------------------------------------

# Marks a repeatable list row/block in templates:
#   <!-- LIST:employee_rows --> ... row HTML with {{employee.*}} ... <!-- /LIST -->
_LIST_RE = re.compile(
    r"<!--\s*LIST:(\w+)\s*-->(.*?)<!--\s*/LIST\s*-->",
    re.DOTALL,
)


@dataclass
class ListRegion:
    region_id: str
    row_template: str


def extract_list_regions(html: str) -> list[ListRegion]:
    return [ListRegion(m.group(1), m.group(2)) for m in _LIST_RE.finditer(html)]


def _ensure_row_index(context: ContextMap) -> None:
    """Default ``row.index`` to ``"1"`` for single-row templates outside LIST regions."""
    row_ns = context.setdefault("row", {})
    row_ns.setdefault("index", "1")


def render_list_region(
    row_template: str,
    rows: list[ContextMap],
) -> str:
    """Render *row_template* for each row context in *rows* and concatenate."""
    rendered_rows: list[str] = []
    for i, row_ctx in enumerate(rows, start=1):
        # Inject row index placeholder {{row.index}}
        row_ctx.setdefault("row", {})["index"] = str(i)
        rendered, _ = render_placeholders(row_template, row_ctx)
        rendered_rows.append(rendered)
    return "".join(rendered_rows)


def render_template(
    template: TemplateMeta,
    context: ContextMap,
    list_data: dict[str, list[ContextMap]] | None = None,
) -> tuple[str, list[str]]:
    """Fully render a template.

    Args:
        template:  The template metadata (for accessing HTML path).
        context:   Top-level context map (namespace → dict).
        list_data: Optional mapping from list-region ID → list of row contexts.

    Returns:
        ``(html_string, missing_keys)``
    """
    html = template.template_html_path.read_text(encoding="utf-8")

    # Render list regions first
    if list_data:
        def list_replacer(m: re.Match) -> str:  # type: ignore[type-arg]
            region_id = m.group(1)
            row_tpl = m.group(2)
            rows = list_data.get(region_id, [])
            if not rows:
                return ""
            return render_list_region(row_tpl, rows)

        html = _LIST_RE.sub(list_replacer, html)

    # Render scalar placeholders (including row.index outside LIST regions)
    _ensure_row_index(context)
    return render_placeholders(html, context)


# ---------------------------------------------------------------------------
# 6.3  HTML → PDF
# ---------------------------------------------------------------------------

_FONT_INJECT = """
<style>
body { font-family: "SimSun", "Songti SC", "STSong", "Source Han Serif CN",
       "PingFang SC", "Heiti SC", "Microsoft YaHei", serif !important; }
</style>
"""


_PRINT_CSS_INJECT = """
<style>
@media print {
  body {
    margin: 0 !important;
    padding: 0 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .page {
    width: 100% !important;
    max-width: 100% !important;
    min-height: 0 !important;
    height: auto !important;
    margin: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    background: transparent !important;
  }
  tr, th, td {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }
  thead {
    display: table-header-group !important;
  }
}
</style>
"""


_PLAYWRIGHT_AVAILABLE: bool | None = None


def _playwright_available() -> bool:
    global _PLAYWRIGHT_AVAILABLE
    if _PLAYWRIGHT_AVAILABLE is None:
        try:
            import playwright  # type: ignore[import, unused-import]  # noqa: F401
            _PLAYWRIGHT_AVAILABLE = True
        except ImportError:
            _PLAYWRIGHT_AVAILABLE = False
    return _PLAYWRIGHT_AVAILABLE


_PDF_MARGIN = {"top": "12mm", "bottom": "12mm", "left": "12mm", "right": "12mm"}


def _prepare_html_for_pdf(html: str) -> str:
    if "</head>" in html:
        return html.replace("</head>", _FONT_INJECT + _PRINT_CSS_INJECT + "</head>", 1)
    return html


def html_to_pdf(html: str, output_path: Path | None = None) -> bytes:
    """Convert *html* to PDF bytes using Playwright (preferred) or weasyprint.

    Args:
        html:         Fully rendered HTML string.
        output_path:  Optional path to save the PDF alongside returning bytes.

    Returns:
        Raw PDF bytes.
    """
    html = _prepare_html_for_pdf(html)
    pdf_bytes = (
        _pdf_via_playwright(html) if _playwright_available() else None
    ) or _pdf_via_weasyprint(html)

    if pdf_bytes and output_path:
        output_path.write_bytes(pdf_bytes)

    return pdf_bytes or b""


def html_contents_to_pdf(contents: list[bytes]) -> list[bytes]:
    """Convert HTML byte blobs to PDF, reusing one Playwright browser for the batch."""
    results: list[bytes] = [b""] * len(contents)
    pending: list[tuple[int, str]] = []

    for idx, content in enumerate(contents):
        if content.startswith(b"%PDF"):
            results[idx] = content
            continue
        stripped = content.lstrip()
        if stripped.startswith(b"<") or stripped.startswith(b"<!"):
            pending.append((idx, _prepare_html_for_pdf(content.decode("utf-8"))))
        else:
            results[idx] = content

    if not pending:
        return results

    batch = _pdf_batch_via_playwright([html for _, html in pending])
    if batch is not None:
        for (idx, _), pdf in zip(pending, batch):
            results[idx] = pdf
        return results

    for idx, html in pending:
        results[idx] = _pdf_via_weasyprint(html) or b""
    return results


def _pdf_via_playwright(html: str) -> bytes | None:
    batch = _pdf_batch_via_playwright([html])
    return batch[0] if batch else None


def _pdf_batch_via_playwright(htmls: list[str]) -> list[bytes] | None:
    if not htmls:
        return []
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import]

        pdfs: list[bytes] = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for html in htmls:
                page.set_content(html, wait_until="domcontentloaded")
                pdfs.append(
                    page.pdf(
                        format="A4",
                        print_background=True,
                        prefer_css_page_size=True,
                        margin=_PDF_MARGIN,
                    )
                )
            browser.close()
        return pdfs
    except Exception as exc:
        logger.warning("Playwright batch PDF failed: %s", exc)
        return None


def _pdf_via_weasyprint(html: str) -> bytes | None:
    try:
        import weasyprint  # type: ignore[import]
        import logging as _logging

        # Suppress WeasyPrint's verbose warnings about missing external resources
        _logging.getLogger("weasyprint").setLevel(_logging.ERROR)
        _logging.getLogger("fontTools").setLevel(_logging.ERROR)
        return weasyprint.HTML(string=html).write_pdf()
    except Exception as exc:
        logger.warning("weasyprint PDF failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# 6.4  Output filename generation
# ---------------------------------------------------------------------------


def build_output_filename(naming_template: str, context: ContextMap, suffix: str = ".pdf") -> str:
    """Resolve ``output_naming`` pattern (same ``{{namespace.key}}`` syntax).

    Falls back to sanitised namespace.key token when a placeholder is missing.
    """
    rendered, missing = render_placeholders(naming_template, context)
    # Sanitise for filesystem use
    safe = re.sub(r'[\\/:*?"<>|]', "_", rendered)
    if not safe.endswith(suffix):
        safe += suffix
    return safe


# ---------------------------------------------------------------------------
# 6.5  Preview (HTML)
# ---------------------------------------------------------------------------


def _preview_orientation_meta(html: str) -> str:
    """Inject orientation hint for the preview iframe scaler."""
    if re.search(r"@page\s*\{[^}]*A4\s+landscape", html, re.IGNORECASE):
        return '<meta name="x-preview-landscape" content="1">'
    return ""


def preview_html(
    template: TemplateMeta,
    context: ContextMap,
    list_data: dict[str, list[ContextMap]] | None = None,
) -> str:
    """Return a rendered HTML string suitable for browser preview.

    Unresolved placeholders are highlighted in red so the user can
    see what data is missing.
    """
    html, missing = render_template(template, context, list_data)

    # Highlight remaining unresolved placeholders
    def highlight(m: re.Match) -> str:  # type: ignore[type-arg]
        return (
            f'<span style="background:#ffe0e0;color:#c00;border:1px dashed #c00;'
            f'padding:0 2px;border-radius:2px;">{m.group(0)}</span>'
        )

    html = _PH_RE.sub(highlight, html)

    orientation_meta = _preview_orientation_meta(html)
    if orientation_meta and "<head>" in html:
        html = html.replace("<head>", f"<head>{orientation_meta}", 1)

    return html
