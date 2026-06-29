"""Regression: content_map must not reuse bytes when DocGenResult ids are recycled."""
from __future__ import annotations

import re
from pathlib import Path

from app.api.generate import _to_content_bytes
from app.core.calendar import WorkCalendar
from app.models.sample_roster_data import sample_employees_as_models
from app.services.hr_generator import DocGenResult, generate_all_hr_docs
from app.services.package_export import build_manifest
from app.services.signature import SignatureStore
from app.templates.loader import TemplateLoader

TEMPLATE_BASE = Path(__file__).resolve().parent.parent.parent / "template"


def _doc_title(html: str) -> str:
    match = re.search(r"font-size:16pt[^>]*>([^<]+)<", html) or re.search(
        r"<title>([^<]+)</title>", html
    )
    return match.group(1) if match else ""


def test_to_content_bytes_does_not_reuse_recycled_object_ids() -> None:
    """Simulate multi-employee generation where ``id()`` gets reused after GC."""
    loader = TemplateLoader(TEMPLATE_BASE)
    employees = sample_employees_as_models()
    enterprise = {"name": "浙江精创汽车零部件有限公司"}
    sig = SignatureStore()
    cal = WorkCalendar()
    cache: dict[tuple[str, str], bytes] = {}

    shentao = next(emp for emp in employees if emp.name == "沈涛")
    hr = generate_all_hr_docs(shentao, loader, enterprise, sig, [2024], cal, None, employees)
    onboarding = [
        r
        for r in hr
        if any(
            token in r.template_id
            for token in ("2新员工入职需知", "3公司入职人员登记表", "4用工合同协议书")
        )
    ]
    probation = [
        r
        for r in hr
        if any(
            token in r.template_id
            for token in (
                "5新员工入职岗位培训评价表",
                "6转正申请表",
                "7技能履历个人管理表",
            )
        )
    ]
    manifest = build_manifest("沈涛", onboarding, probation, [], [], [])

    # Warm cache with every other employee's documents (mirrors /generate/ loop).
    for emp in employees:
        if emp.name == "沈涛":
            continue
        other = generate_all_hr_docs(emp, loader, enterprise, sig, [2024], cal, None, employees)
        for result in other:
            _to_content_bytes(result, cache)

    expected = {
        "2新员工入职需知": "新员工入职需知",
        "3公司入职人员登记表": "公司入职人员登记表",
        "4用工合同协议书": "用工合同协议书",
        "5新员工入职岗位培训评价表": "新员工入职岗位培训评价表",
        "6转正申请表": "转正申请表",
        "7技能履历个人管理表": "技能履历",
    }

    for entry in manifest.entries:
        matched = next(
            (
                r
                for r in hr
                if r.output_filename and entry.filename.endswith(r.output_filename)
            ),
            None,
        )
        assert matched is not None
        stored = _to_content_bytes(matched, cache).decode("utf-8")
        title = _doc_title(stored)
        for token, fragment in expected.items():
            if token in entry.filename:
                assert fragment in title, f"{entry.filename}: got {title!r}"
                break
