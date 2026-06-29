"""Data namespace registry for template placeholder resolution.

Defines the canonical set of namespaces and their allowed keys used
in ``{{namespace.key}}`` placeholders across all templates.
"""
from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Namespace names
# ---------------------------------------------------------------------------

NS_ENTERPRISE: Final = "enterprise"
NS_EMPLOYEE: Final = "employee"
NS_CONTRACT: Final = "contract"
NS_TRAINING: Final = "training"
NS_SIGNATURE: Final = "signature"
NS_DOCUMENT: Final = "document"
NS_INCENTIVE: Final = "incentive"
NS_POSITION_SAFETY: Final = "position_safety"
NS_ONBOARDING: Final = "onboarding"
NS_ROW: Final = "row"

KNOWN_NAMESPACES: Final[frozenset[str]] = frozenset(
    {
        NS_ENTERPRISE,
        NS_EMPLOYEE,
        NS_CONTRACT,
        NS_TRAINING,
        NS_SIGNATURE,
        NS_DOCUMENT,
        NS_INCENTIVE,
        NS_POSITION_SAFETY,
        NS_ONBOARDING,
        NS_ROW,
    }
)

# ---------------------------------------------------------------------------
# Per-namespace canonical key sets
# ---------------------------------------------------------------------------

ENTERPRISE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "name",           # 企业名称
        "short_name",     # 企业简称
        "address",        # 企业地址
        "legal_rep",      # 法定代表人
        "contact",        # 联系人
        "phone",          # 联系电话
        "year",           # 当前审核年度
    }
)

EMPLOYEE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "name",               # 姓名
        "department_name",    # 部门
        "position_name",      # 岗位名称
        "position_category",  # 岗位类别
        "gender",             # 性别
        "id_no",              # 身份证号
        "birth_date",         # 出生年月（可从身份证推导）
        "hire_date",          # 入职日期
        "phone",              # 联系电话
        "education",          # 学历
        "school",             # 毕业院校
        "address",            # 家庭住址
        "remark",             # 备注
        "is_key_position",    # 是否重点岗位
        "is_internal_auditor",# 是否内审员
        "is_regular_employee",# 是否普通员工
        "is_manager",         # 是否管理人员
        "employment_status",  # 在职状态
        "signature",          # 签名（图片 base64 或文本回退）
        "probation_end_date", # 转正日期（推导）
        "probation_period",   # 试用期区间（入职日至转正日）
    }
)

CONTRACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "start_date",     # 合同开始日期
        "end_date",       # 合同结束日期
        "duration_years", # 合同期限（年）
        "type",           # 合同类型
    }
)

TRAINING_KEYS: Final[frozenset[str]] = frozenset(
    {
        "course_name",       # 课程名称
        "date",              # 培训日期
        "duration_hours",    # 培训时长（小时）
        "trainer",           # 培训讲师
        "location",          # 培训地点
        "target_audience",   # 面向对象
        "year",              # 培训年度
        "plan_type",         # 计划类型（annual/new_employee）
        "exam.score",        # 考核成绩
        "exam.pass",         # 是否通过
        "exam.date",         # 考核日期
    }
)

SIGNATURE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "manager",           # 部门经理签名
        "hr_manager",        # 人力资源主管签名
        "legal_rep",         # 法定代表人签名
        "supervisor",        # 直属上级签名
        "safety_officer",    # 安全员签名
        "department_head",   # 部门负责人签名（按员工部门解析）
        "general_manager",   # 总经理签名
        "prepared_by",       # 编制人（年培训计划：体系专员或培训部门）
        "reviewed_by",       # 审核人（年培训计划：总经理）
        "approved_by",       # 批准人（年培训计划：总经理）
    }
)

DOCUMENT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "date",          # 文档日期
        "year",          # 文档年度
        "month",         # 文档月份
        "seq_no",        # 序号
        "title",         # 文档标题
    }
)

INCENTIVE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "suggestion_no",
        "suggestion_category",
        "suggestion_topic",
        "suggestion_current_state",
        "suggestion_content",
        "suggestion_expected_effect",
        "suggestion_review_opinion",
        "process_name",
        "nonconformity_clause",
        "nonconformity_severity",
        "dissatisfaction_description",
        "root_cause_analysis",
        "corrective_action",
        "corrective_implementation",
        "corrective_verification",
        "survey_year",
        "date",
        "content",
        "result",
    }
)

POSITION_SAFETY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "month_label",    # 月份标签（如 "2024年1月"）
        "check_date",     # 检查日期
        "checker",        # 检查人
        "issues",         # 发现问题
        "actions",        # 整改措施
        "rectification_notes", # 问题及整改情况
        "inspection_year",     # 检查年度
    }
)

ONBOARDING_KEYS: Final[frozenset[str]] = frozenset(
    {
        "category",           # 培训项目
        "content",            # 培训/考核内容
        "date",               # 培训时间
        "department",         # 培训部门
        "trainer",            # 培训人
        "conclusion",         # 培训结论
        "meets_requirement",  # 是否满足上岗要求
    }
)

ROW_KEYS: Final[frozenset[str]] = frozenset(
    {
        "index",  # 列表行序号（LIST 区域循环时自动递增，单行模板默认为 1）
    }
)

# ---------------------------------------------------------------------------
# Combined registry: namespace -> canonical keys
# ---------------------------------------------------------------------------

NAMESPACE_KEYS: Final[dict[str, frozenset[str]]] = {
    NS_ENTERPRISE: ENTERPRISE_KEYS,
    NS_EMPLOYEE: EMPLOYEE_KEYS,
    NS_CONTRACT: CONTRACT_KEYS,
    NS_TRAINING: TRAINING_KEYS,
    NS_SIGNATURE: SIGNATURE_KEYS,
    NS_DOCUMENT: DOCUMENT_KEYS,
    NS_INCENTIVE: INCENTIVE_KEYS,
    NS_POSITION_SAFETY: POSITION_SAFETY_KEYS,
    NS_ONBOARDING: ONBOARDING_KEYS,
    NS_ROW: ROW_KEYS,
}


def is_known_placeholder(namespace: str, key: str) -> bool:
    """Return True if *namespace.key* exists in the canonical registry."""
    ns_keys = NAMESPACE_KEYS.get(namespace)
    if ns_keys is None:
        return False
    # Support dotted sub-keys (e.g. training.exam.score)
    return key in ns_keys or any(k.startswith(key + ".") or key.startswith(k) for k in ns_keys)
