"""Tests for template preview sample context."""
from __future__ import annotations

from pathlib import Path

from app.services.renderer import preview_html
from app.services.sample_context import build_sample_context, build_sample_list_data
from app.templates.loader import TemplateLoader

TEMPLATE_BASE = Path(__file__).parent.parent.parent / "template"

TMPL_SUGGESTION = "20员工激励__2024年度员工满意度调查分析报告-xls__1合理化建议表"
TMPL_DISSATISFACTION = (
    "20员工激励__2024年度员工满意度调查分析报告-xls__员工不满意项目纠正和预防措施表"
)
TMPL_ROSTER = "16员工档案__员工档案文件资料-xlsx__8人员花名册"
TMPL_ATTENDANCE = "18培训计划__培训记录__2024年培训记录-空白表单-xlsx__培训记录"


def test_preview_resolves_incentive_placeholders() -> None:
    loader = TemplateLoader(TEMPLATE_BASE)
    ctx = build_sample_context()

    for tmpl_id in (TMPL_SUGGESTION, TMPL_DISSATISFACTION):
        tmpl = loader.get_by_id(tmpl_id)
        assert tmpl is not None
        html = preview_html(tmpl, ctx)
        assert "{{incentive." not in html
        assert "background:#ffe0e0" not in html


def test_preview_resolves_row_index() -> None:
    loader = TemplateLoader(TEMPLATE_BASE)
    tmpl = loader.get_by_id(TMPL_ROSTER)
    assert tmpl is not None
    html = preview_html(
        tmpl,
        build_sample_context(),
        build_sample_list_data(TMPL_ROSTER),
    )
    assert "{{row.index}}" not in html
    assert "background:#ffe0e0" not in html
    assert "<td>1</td>" in html
    assert "<td>2</td>" in html


def test_preview_resolves_training_record_placeholders() -> None:
    loader = TemplateLoader(TEMPLATE_BASE)
    tmpl = loader.get_by_id(TMPL_ATTENDANCE)
    assert tmpl is not None
    html = preview_html(
        tmpl,
        build_sample_context(),
        build_sample_list_data(TMPL_ATTENDANCE),
    )
    assert "{{training." not in html
    assert "{{employee." not in html
    assert "2024年03月01日" in html
    assert "示例培训内容" in html
    assert "培训有效" in html
    assert "张三（示例）" in html
    assert "李四（示例）" in html
