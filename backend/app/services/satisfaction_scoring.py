"""Employee satisfaction survey scoring aligned with the reference analysis report.

Generates per-respondent 1–5 scores whose item means match the published
statistics in ``2024年度员工满意度调查分析报告`` (overall ≈ 3.52).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Reference statistics (46-item analysis report)
# ---------------------------------------------------------------------------

OVERALL_SATISFACTION = 3.52

DIMENSION_SCORES: dict[str, float] = {
    "工作环境": 3.67,
    "薪酬福利": 3.20,
    "职业发展": 3.43,
    "管理与沟通": 3.55,
    "企业文化": 3.65,
}

REPORT_ITEMS: list[tuple[str, float]] = [
    ("公司的工作环境(办公室、车间等)整洁。", 3.8),
    ("我对目前的工作岗位和工作内容感到满意。", 3.7),
    ("我能充分发挥自己的专业技能和特长。", 3.5),
    ("公司有完善的规章制度并能得到有效执行。", 3.6),
    ("部门负责人对下属的工作给予指导和支持。", 3.8),
    ("部门内部沟通顺畅，协作良好。", 3.7),
    ("公司各部门之间配合默契，办事效率高。", 3.4),
    ("公司为员工提供了必要的入职培训和技能培训。", 3.6),
    ("公司有明确的晋升通道和职业发展规划。", 3.2),
    ("我对公司目前提供的培训机会感到满意。", 3.4),
    ("我在公司有不断学习和成长的空间。", 3.5),
    ("我对目前的薪资水平感到满意。", 3.0),
    ("公司的绩效考核制度公平、公正、公开。", 3.2),
    ("公司的福利待遇(五险一金、带薪年假等)较好。", 3.4),
    ("薪资发放准时，没有任何拖欠现象。", 4.2),
    ("我认同公司的企业文化和核心价值观。", 3.8),
    ("公司经常组织各类员工活动，增强团队凝聚力。", 3.6),
    ("我在公司工作有安全感和归属感。", 3.7),
    ("我愿意向亲友推荐来公司工作。", 3.5),
    ("公司的加班安排合理，能够保证员工休息。", 3.2),
    ("工作压力适中，不会影响身心健康。", 3.4),
    ("公司尊重员工的个人隐私和合法权益。", 3.8),
    ("我对目前的作息时间安排感到满意。", 3.6),
    ("公司的食堂伙食较好，卫生达标。", 3.4),
    ("公司的宿舍环境舒适，设施齐全。", 3.2),
    ("公司的通勤班车(或交通补贴)方便。", 3.5),
    ("我对公司的后勤保障服务感到满意。", 3.6),
    ("我对公司的整体管理水平感到满意。", 3.5),
    ("我对公司的发展前景充满信心。", 3.8),
    ("我对公司的整体满意度评价。", 3.6),
    ("部门负责人能够虚心听取员工意见。", 3.7),
    ("工作中遇到的问题能得到及时解决。", 3.5),
    ("办公设备(电脑、打印机等)满足工作需要。", 3.8),
    ("公司内部信息传递及时、准确。", 3.4),
    ("公司重视安全生产，劳动保护措施到位。", 4.0),
    ("工作场所通风、采光良好，噪音在控制范围内。", 3.8),
    ("公司定期组织员工体检。", 3.6),
    ("我对公司的安全卫生状况感到满意。", 3.9),
    ("公司的激励机制有效提高了我的工作积极性。", 3.3),
    ("表现优秀者能得到及时的表彰和奖励。", 3.4),
    ("公司的评优评先过程公平透明。", 3.5),
    ("我对公司的奖励制度感到满意。", 3.4),
    ("公司领导经常深入基层了解情况。", 3.2),
    ("员工诉求渠道通畅，反馈及时。", 3.3),
    ("公司重大人事变动或政策调整会提前告知。", 3.4),
    ("我对公司的沟通机制感到满意。", 3.4),
]

REPORT_ITEM_SCORES: list[float] = [score for _, score in REPORT_ITEMS]

# 50-item survey form targets (mean ≈ 3.52, profile aligned with report dimensions)
SURVEY_FORM_TARGETS: list[float] = [
    3.8, 3.7, 3.6, 3.5,
    3.8, 3.7, 3.6, 3.5, 3.8, 3.6, 3.5, 3.2,
    3.6, 3.4, 3.2, 3.6, 3.4,
    3.6, 3.5, 3.5, 3.5, 3.6, 3.5, 3.5, 3.4,
    3.4, 3.4, 3.6, 3.0, 3.2, 3.8, 3.8,
    3.6, 3.4, 3.5, 3.4, 3.8, 3.7, 3.4, 3.7,
    3.7, 3.5, 3.6, 3.6,
    3.5, 3.4, 3.5, 3.4, 3.2, 3.4,
]

STRENGTH_ITEMS: list[tuple[int, str, float]] = [
    (15, "薪资发放准时", 4.2),
    (35, "安全生产重视", 4.0),
    (1, "工作环境整洁", 3.8),
]

WEAKNESS_ITEMS: list[tuple[int, str, float]] = [
    (12, "薪资水平满意度较低", 3.0),
    (9, "晋升通道不明确", 3.2),
    (20, "加班安排有待优化", 3.2),
]

IMPROVEMENT_SUGGESTIONS: list[str] = [
    "优化薪酬体系，提高市场竞争力。",
    "完善晋升机制，为员工提供更多发展空间。",
    "加强内部沟通，提高跨部门协作效率。",
    "关注员工身心健康，合理安排加班时间。",
]

CONCLUSION_TEXT = (
    "本次员工满意度调查总体得分为3.52分，处于中等偏上水平。"
    "员工对公司工作环境、企业文化及薪资发放准时性等方面认可度较高；"
    "薪酬水平、晋升通道及加班安排等方面仍有提升空间。"
    "建议针对薄弱环节制定改进措施，持续提升员工满意度。"
)


@dataclass(frozen=True)
class AggregateStats:
    item_means: list[float]
    overall: float

    def deviation_from(self, targets: list[float]) -> float:
        if len(self.item_means) != len(targets):
            raise ValueError("target length mismatch")
        return max(abs(a - b) for a, b in zip(self.item_means, targets))


def _distribute_scores(n: int, target: float, rng: random.Random) -> list[int]:
    """Return *n* integer scores in [1, 5] whose mean matches *target*."""
    if n <= 0:
        return []
    target_sum = round(target * n)
    target_sum = max(n, min(5 * n, target_sum))

    scores = [max(1, min(5, int(target)))] * n
    diff = target_sum - sum(scores)
    indices = list(range(n))
    rng.shuffle(indices)

    guard = 0
    while diff != 0 and guard < n * 20:
        guard += 1
        idx = indices[guard % n]
        if diff > 0 and scores[idx] < 5:
            scores[idx] += 1
            diff -= 1
        elif diff < 0 and scores[idx] > 1:
            scores[idx] -= 1
            diff += 1

    return scores


def generate_respondent_scores(
    respondent_keys: list[str],
    item_targets: list[float] | None = None,
) -> dict[str, list[int]]:
    """Assign 1–5 scores per respondent so each item mean matches *item_targets*."""
    targets = item_targets or SURVEY_FORM_TARGETS
    if not respondent_keys:
        return {}

    n = len(respondent_keys)
    per_respondent: dict[str, list[int]] = {key: [] for key in respondent_keys}

    for item_idx, target in enumerate(targets):
        rng = random.Random(item_idx * 9973 + n * 131)
        item_scores = _distribute_scores(n, target, rng)
        rng.shuffle(item_scores)
        for key, score in zip(respondent_keys, item_scores):
            per_respondent[key].append(score)

    return per_respondent


def compute_aggregate_stats(
    respondent_scores: dict[str, list[int]],
    item_count: int | None = None,
) -> AggregateStats:
    """Compute per-item and overall means from respondent score maps."""
    if not respondent_scores:
        count = item_count or len(SURVEY_FORM_TARGETS)
        return AggregateStats(item_means=[0.0] * count, overall=0.0)

    keys = sorted(respondent_scores.keys())
    n_items = len(respondent_scores[keys[0]])
    item_sums = [0] * n_items
    for key in keys:
        row = respondent_scores[key]
        for i, score in enumerate(row):
            item_sums[i] += score

    n = len(keys)
    item_means = [round(s / n, 2) for s in item_sums]
    overall = round(sum(item_means) / n_items, 2)
    return AggregateStats(item_means=item_means, overall=overall)


def build_survey_mark_context(scores: list[int]) -> dict[str, str]:
    """Map integer scores to checkmark placeholders for the 50-item survey form."""
    ctx: dict[str, str] = {}
    for idx, score in enumerate(scores, start=1):
        for level in range(1, 6):
            ctx[f"q{idx:02d}_c{level}"] = "√" if score == level else ""
    return ctx


def build_analysis_report_context(
    *,
    survey_year: int,
    survey_month: str = "6",
    report_date: str = "",
    enterprise_name: str = "",
    hr_manager: str = "",
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Build render context and list data for the analysis report template."""
    if not report_date:
        report_date = f"{survey_year}年7月5日"

    report_rows: list[dict[str, Any]] = []
    for i, (text, score) in enumerate(REPORT_ITEMS, start=1):
        report_rows.append({
            "report": {"item_text": text, "item_score": f"{score:.1f}"},
            "row": {"index": str(i)},
        })

    dim_lines = "；".join(f"{name}{score:.2f}分" for name, score in DIMENSION_SCORES.items())
    strength_lines = "；".join(
        f"{label}（第{num}项，{score:.1f}分）" for num, label, score in STRENGTH_ITEMS
    )
    weakness_lines = "；".join(
        f"{label}（第{num}项，{score:.1f}分）" for num, label, score in WEAKNESS_ITEMS
    )
    suggestions = "\n".join(f"{i + 1}、{text}" for i, text in enumerate(IMPROVEMENT_SUGGESTIONS))

    context: dict[str, Any] = {
        "enterprise": {"name": enterprise_name, "year": str(survey_year)},
        "document": {
            "date": report_date,
            "year": str(survey_year),
            "month": survey_month,
        },
        "incentive": {
            "survey_year": str(survey_year),
            "survey_month": survey_month,
            "overall_score": f"{OVERALL_SATISFACTION:.2f}",
            "dimension_summary": dim_lines,
            "strength_summary": strength_lines,
            "weakness_summary": weakness_lines,
            "improvement_suggestions": suggestions,
            "conclusion": CONCLUSION_TEXT,
        },
        "signature": {"hr_manager": hr_manager},
    }
    return context, {"report_items": report_rows}
