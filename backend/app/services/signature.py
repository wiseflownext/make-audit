"""Signature processing module.

Tasks 5.1 – 5.4:
  5.1  Upload + employee mapping  (in-memory store keyed by employee name)
  5.2  Background removal → transparent PNG via rembg (Pillow fallback)
  5.3  Text-signature fallback when no image is uploaded
  5.4  Unified render value: base64 data-URI or CSS text-signature marker
"""
from __future__ import annotations

import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 5.1  Signature store (in-memory, keyed by employee name)
# ---------------------------------------------------------------------------


_SIGNATURES_DIR = Path(__file__).parent.parent.parent / "data" / "signatures"


class SignatureStore:
    """In-memory store mapping employee name → transparent PNG bytes, backed by disk."""

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}
        self._load_from_disk()

    def _sig_path(self, employee_name: str) -> Path:
        safe = employee_name.strip().replace("/", "_").replace("\\", "_")
        return _SIGNATURES_DIR / f"{safe}.png"

    def _load_from_disk(self) -> None:
        """Load all existing signature files from disk into memory."""
        try:
            _SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)
            for sig_file in _SIGNATURES_DIR.glob("*.png"):
                name = sig_file.stem
                try:
                    self._store[name] = sig_file.read_bytes()
                except Exception as exc:
                    logger.warning("Failed to load signature %s: %s", sig_file, exc)
        except Exception as exc:
            logger.warning("Failed to load signatures from disk: %s", exc)

    def _save_to_disk(self, employee_name: str, png_bytes: bytes) -> None:
        try:
            _SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)
            self._sig_path(employee_name).write_bytes(png_bytes)
        except Exception as exc:
            logger.warning("Failed to save signature for %s: %s", employee_name, exc)

    def _delete_from_disk(self, employee_name: str) -> None:
        try:
            path = self._sig_path(employee_name)
            if path.exists():
                path.unlink()
        except Exception as exc:
            logger.warning("Failed to delete signature for %s: %s", employee_name, exc)

    def add(self, employee_name: str, image_bytes: bytes, filename: str = "") -> None:
        """Process *image_bytes* (any PIL-supported format) and store as transparent PNG."""
        png = remove_background(image_bytes)
        name = employee_name.strip()
        self._store[name] = png
        self._save_to_disk(name, png)

    def store_raw(self, employee_name: str, png_bytes: bytes) -> None:
        """Store raw PNG bytes directly (e.g. from canvas pad) and persist to disk."""
        name = employee_name.strip()
        self._store[name] = png_bytes
        self._save_to_disk(name, png_bytes)

    def get(self, employee_name: str) -> bytes | None:
        return self._store.get(employee_name.strip())

    def names(self) -> list[str]:
        return list(self._store.keys())

    def delete(self, employee_name: str) -> None:
        name = employee_name.strip()
        self._store.pop(name, None)
        self._delete_from_disk(name)

    def clear(self) -> None:
        for name in list(self._store.keys()):
            self._delete_from_disk(name)
        self._store.clear()

    def export_zip(self) -> bytes:
        """Export all signatures as a ZIP archive."""
        import io
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, png in self._store.items():
                zf.writestr(f"{name}.png", png)
        return buf.getvalue()


# ---------------------------------------------------------------------------
# 5.2  Background removal
# ---------------------------------------------------------------------------


def _try_import_rembg() -> Any | None:
    """Return the rembg module if usable, otherwise None."""
    import sys
    import os

    try:
        # rembg prints to stderr and may call sys.exit when onnxruntime is missing;
        # redirect stderr temporarily to suppress the noise.
        devnull = open(os.devnull, "w")
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            import rembg as _rembg  # type: ignore[import]
        finally:
            sys.stderr = old_stderr
            devnull.close()
        return _rembg
    except (ImportError, SystemExit, Exception):
        return None


_rembg_module: Any | None = _try_import_rembg()
if _rembg_module is None:
    logger.warning("rembg not available; will use Pillow white-threshold background removal.")


def remove_background(image_bytes: bytes) -> bytes:
    """Remove background from *image_bytes* and return transparent PNG bytes.

    Uses ``rembg`` when available; falls back to simple white-threshold removal
    via Pillow when rembg is not installed or lacks onnxruntime.
    """
    if _rembg_module is not None:
        try:
            result = _rembg_module.remove(image_bytes)
            return result  # rembg returns PNG bytes
        except Exception as exc:
            logger.warning("rembg failed (%s); falling back to Pillow.", exc)
    return _pillow_remove_white(image_bytes)


def _pillow_remove_white(image_bytes: bytes, threshold: int = 240) -> bytes:
    """Simple white-background removal using Pillow.

    Pixels whose R, G and B are all ≥ *threshold* are made transparent.
    """
    from PIL import Image  # type: ignore[import]

    img = Image.open(BytesIO(image_bytes)).convert("RGBA")
    data = img.getdata()
    new_data: list[tuple[int, int, int, int]] = []
    for r, g, b, a in data:  # type: ignore[misc]
        if r >= threshold and g >= threshold and b >= threshold:
            new_data.append((255, 255, 255, 0))  # transparent
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)  # type: ignore[arg-type]
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 5.3  Text signature fallback
# ---------------------------------------------------------------------------

_HANDWRITING_FONT_CSS = (
    "'ZCOOL QingKe HuangYou', 'STXingkai', 'KaiTi', 'AR PL UKai CN', cursive"
)


def text_signature_html(name: str) -> str:
    """Return an inline HTML snippet rendering *name* in a handwriting-style font.

    This value is injected into the template as a non-printing-style signature.
    """
    safe = name.replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'<span style="font-family:{_HANDWRITING_FONT_CSS};'
        f'font-size:1.2em;color:#1a1a1a;">{safe}</span>'
    )


# ---------------------------------------------------------------------------
# 5.4  Unified signature render value
# ---------------------------------------------------------------------------


def signature_render_value(employee_name: str, store: SignatureStore) -> str:
    """Return the render value for ``{{employee.signature}}``.

    - If an image is found in *store*: returns an ``<img>`` tag with base64 PNG.
    - Otherwise: returns a text-signature HTML fallback.
    """
    png = store.get(employee_name)
    if png:
        b64 = base64.b64encode(png).decode("ascii")
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="height:2em;vertical-align:middle;" alt="签名"/>'
        )
    return text_signature_html(employee_name)


def manager_signature_render_value(
    role_key: str,
    manager_name: str,
    store: SignatureStore,
) -> str:
    """Return the render value for ``{{signature.<role_key>}}``.

    Looks up *manager_name* in *store*; falls back to text signature.
    """
    return signature_render_value(manager_name, store)
