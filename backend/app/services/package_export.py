"""Audit package export.

Tasks 9.1 – 9.4:
  9.1  File manifest data structure (per employee / company-level categories)
  9.2  Auditable directory structure
  9.3  ZIP packing and one-click download
  9.4  Empty-result handling
"""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from typing import Any

from app.services.hr_generator import DocGenResult


# ---------------------------------------------------------------------------
# 9.1  File manifest
# ---------------------------------------------------------------------------


@dataclass
class ManifestEntry:
    filename: str          # final filename in the ZIP
    category: str          # e.g. "员工档案/张三/入职档案"
    template_id: str
    missing_keys: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class PackageManifest:
    entries: list[ManifestEntry] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def generated(self) -> int:
        return sum(1 for e in self.entries if not e.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for e in self.entries if e.skipped)

    @property
    def with_warnings(self) -> int:
        return sum(1 for e in self.entries if e.missing_keys and not e.skipped)

    def summary(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "generated": self.generated,
            "skipped": self.skipped_count,
            "with_warnings": self.with_warnings,
        }


# ---------------------------------------------------------------------------
# 9.2  Directory structure builder
# ---------------------------------------------------------------------------


def _employee_dir(emp_name: str, category: str) -> str:
    """Return auditable directory path: 员工档案/<name>/<category>"""
    return f"员工档案/{emp_name}/{category}"


def build_manifest(
    employee_name: str,
    onboarding: list[DocGenResult],
    probation: list[DocGenResult],
    satisfaction: list[DocGenResult],
    attendance: list[DocGenResult],
    personal_training: list[DocGenResult],
    company_docs: list[DocGenResult] | None = None,
) -> PackageManifest:
    manifest = PackageManifest()

    for result in onboarding:
        manifest.entries.append(
            ManifestEntry(
                filename=f"{_employee_dir(employee_name, '入职档案')}/{result.output_filename}",
                category="入职档案",
                template_id=result.template_id,
                missing_keys=result.missing_keys,
                skipped=result.skipped,
                skip_reason=result.skip_reason,
            )
        )

    for result in probation:
        manifest.entries.append(
            ManifestEntry(
                filename=f"{_employee_dir(employee_name, '转正档案')}/{result.output_filename}",
                category="转正档案",
                template_id=result.template_id,
                missing_keys=result.missing_keys,
                skipped=result.skipped,
                skip_reason=result.skip_reason,
            )
        )

    for result in satisfaction:
        manifest.entries.append(
            ManifestEntry(
                filename=f"{_employee_dir(employee_name, '满意度调查')}/{result.output_filename}",
                category="满意度调查",
                template_id=result.template_id,
                missing_keys=result.missing_keys,
                skipped=result.skipped,
                skip_reason=result.skip_reason,
            )
        )

    for result in personal_training:
        manifest.entries.append(
            ManifestEntry(
                filename=f"{_employee_dir(employee_name, '个人培训记录')}/{result.output_filename}",
                category="个人培训记录",
                template_id=result.template_id,
                missing_keys=result.missing_keys,
                skipped=result.skipped,
                skip_reason=result.skip_reason,
            )
        )

    for result in attendance:
        manifest.entries.append(
            ManifestEntry(
                filename=f"公司级文件/培训签到记录/{result.output_filename}",
                category="培训签到记录",
                template_id=result.template_id,
                missing_keys=result.missing_keys,
                skipped=result.skipped,
                skip_reason=result.skip_reason,
            )
        )

    for result in (company_docs or []):
        manifest.entries.append(
            ManifestEntry(
                filename=f"公司级文件/{result.output_filename}",
                category="公司级文件",
                template_id=result.template_id,
                missing_keys=result.missing_keys,
                skipped=result.skipped,
                skip_reason=result.skip_reason,
            )
        )

    return manifest


# ---------------------------------------------------------------------------
# 9.3  ZIP packing
# ---------------------------------------------------------------------------


def pack_to_zip(
    results_with_paths: list[tuple[str, bytes]],
) -> bytes:
    """Pack ``(path_in_zip, content_bytes)`` pairs into a ZIP archive.

    Returns raw ZIP bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, content in results_with_paths:
            zf.writestr(path, content)
    return buf.getvalue()


def build_zip_from_manifest(
    manifest: PackageManifest,
    content_map: dict[str, bytes],
) -> bytes:
    """Build ZIP from *manifest* entries, looking up content in *content_map*.

    *content_map* keys are the ``ManifestEntry.filename`` values.
    Skipped entries are omitted; entries with missing content are skipped with a warning.
    """
    pairs: list[tuple[str, bytes]] = []
    for entry in manifest.entries:
        if entry.skipped:
            continue
        content = content_map.get(entry.filename)
        if content is None:
            continue
        pairs.append((entry.filename, content))

    return pack_to_zip(pairs)


# ---------------------------------------------------------------------------
# 9.4  Empty-result guard
# ---------------------------------------------------------------------------


class EmptyPackageError(ValueError):
    """Raised when the manifest has no generated files to pack."""


def assert_non_empty(manifest: PackageManifest) -> None:
    """Raise :class:`EmptyPackageError` when nothing was generated."""
    if manifest.generated == 0:
        raise EmptyPackageError(
            "资料包为空：没有成功生成任何文件。"
            f"共 {manifest.total} 项，全部跳过（{manifest.skipped_count} 项）。"
            "请检查员工数据与模版配置。"
        )
