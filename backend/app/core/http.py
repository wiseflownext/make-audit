"""HTTP response helpers."""
from __future__ import annotations

from urllib.parse import quote


def attachment_disposition(filename: str) -> dict[str, str]:
    """Build a Content-Disposition header safe for non-ASCII filenames."""
    quoted = quote(filename)
    if quoted != filename:
        value = f"attachment; filename*=utf-8''{quoted}"
    else:
        value = f'attachment; filename="{filename}"'
    return {"Content-Disposition": value}
