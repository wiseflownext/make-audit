"""Sample context for template preview and validation demos."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _fmt_date(raw: str | date) -> str:
    if isinstance(raw, date):
        return raw.strftime("%Y年%m月%d日")
    text = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y年%m月%d日")
        except ValueError:
            continue
    return text


def _fallback_incentive() -> dict[str, str]:
    return {
        "suggestion_category": "现场管理",
        "suggestion_topic": "机加工区域刀具摆放标准化",
        "suggestion_current_state": "目前机加工现场刀具混放，换刀时需在各工位间寻找，平均换刀时间约8分钟。",
        "suggestion_content": "建议在每台设备旁设置刀具定置盒，按工序编号贴标签，并绘制刀具摆放示意图。",
        "suggestion_expected_effect": "预计换刀时间缩短至3分钟以内，减少刀具错用导致的废品率。",
        "suggestion_review_opinion": "建议切实可行，同意采纳。由生产部负责在3月底前完成定置盒配置及标识。",
        "process_name": "生产过程",
        "nonconformity_clause": "8.5.1.1 生产和服务提供的控制",
        "nonconformity_severity": "一般",
        "dissatisfaction_description": "满意度调查中多名员工反映机加工现场刀具、量具摆放混乱，找工具耗时长。",
        "root_cause_analysis": "1. 现场缺乏统一的定置管理标准；2. 班组长日常检查频次不足。",
        "corrective_action": "1. 制定《机加工现场定置管理规范》；2. 配置定置盒及标识。",
        "corrective_implementation": "已完成定置盒采购及安装，全部28台设备旁均已配置。",
        "corrective_verification": "经现场抽查及员工回访，找工具时间明显缩短，纠正措施有效。",
        "analyst_name": "示例分析员",
        "analyst_date": "2024年02月21日",
        "action_owner": "示例负责人",
        "action_date": "2024年02月25日",
        "implementer_name": "示例实施人",
        "implementer_date": "2024年03月03日",
        "verifier_name": "示例验证人",
        "verifier_date": "2024年03月10日",
        "survey_year": str(date.today().year),
        "survey_month": "6",
        "overall_score": "3.52",
        "dimension_summary": "工作环境3.67分；薪酬福利3.20分；职业发展3.43分；管理与沟通3.55分；企业文化3.65分",
        "strength_summary": "薪资发放准时（第15项，4.2分）；安全生产重视（第35项，4.0分）；工作环境整洁（第1项，3.8分）",
        "weakness_summary": "薪资水平满意度较低（第12项，3.0分）；晋升通道不明确（第9项，3.2分）；加班安排有待优化（第20项，3.2分）",
        "improvement_suggestions": "1、优化薪酬体系，提高市场竞争力。\n2、完善晋升机制，为员工提供更多发展空间。\n3、加强内部沟通，提高跨部门协作效率。\n4、关注员工身心健康，合理安排加班时间。",
        "conclusion": (
            "本次员工满意度调查总体得分为3.52分，处于中等偏上水平。"
            "员工对公司工作环境、企业文化及薪资发放准时性等方面认可度较高；"
            "薪酬水平、晋升通道及加班安排等方面仍有提升空间。"
        ),
    }


def _incentive_from_json() -> dict[str, str]:
    try:
        from app.services.incentive_generator import load_incentive_pairs

        pairs = load_incentive_pairs()
        if not pairs:
            return _fallback_incentive()
        pair = pairs[0]
        incentive = {
            **_fallback_incentive(),
            **pair.get("dissatisfaction", {}),
            **pair.get("suggestion", {}),
        }
        incentive["survey_year"] = str(date.today().year)
        return incentive
    except Exception:
        return _fallback_incentive()


def _build_sample_signature_context() -> dict[str, str]:
    """Sample management signatures derived from the standard 52-person roster."""
    from app.models.sample_roster_data import sample_employees_as_models
    from app.services.hr_generator import (
        find_department_head_name,
        find_hr_manager_name,
        resolve_manager_map,
    )

    employees = sample_employees_as_models()
    resolved = resolve_manager_map({}, employees)
    sample_employee = next(
        (emp for emp in employees if emp.department_name == "生产部" and not emp.is_manager),
        employees[0],
    )
    department_head = find_department_head_name(
        sample_employee.department_name,
        employees,
        exclude_name=sample_employee.name,
    )

    return {
        "manager": department_head or "李经理（示例）",
        "hr_manager": resolved.get("hr_manager", "王HR（示例）"),
        "legal_rep": "赵总（示例）",
        "supervisor": department_head or "李经理（示例）",
        "safety_officer": "张安全员（示例）",
        "department_head": department_head or "李经理（示例）",
        "general_manager": resolved.get("general_manager", "陈建国（示例）"),
        "prepared_by": resolved.get("prepared_by", "孙丽（示例）"),
        "reviewed_by": resolved.get("reviewed_by", resolved.get("general_manager", "陈建国（示例）")),
        "approved_by": resolved.get("approved_by", resolved.get("general_manager", "陈建国（示例）")),
    }


def build_sample_context() -> dict[str, Any]:
    """Return a complete sample context covering all template namespaces."""
    today = date.today()
    incentive = _incentive_from_json()
    doc_date = "2024年02月18日"
    try:
        from app.services.incentive_generator import load_incentive_pairs

        pairs = load_incentive_pairs()
        if pairs and pairs[0].get("document_date"):
            doc_date = _fmt_date(pairs[0]["document_date"])
    except Exception:
        pass

    from app.services.training_generator import TRAINING_EFFECTIVENESS_EVALUATION

    ctx: dict[str, Any] = {
        "enterprise": {"name": "示例企业有限公司", "year": str(today.year)},
        "employee": {
            "name": "张三（示例）",
            "department_name": "生产部",
            "position_name": "操作工",
            "position_category": "生产类",
            "hire_date": "2024年01月15日",
            "gender": "男",
            "id_no": "330102199001011234",
            "birth_date": "1990年01月01日",
            "phone": "13812345678",
            "education": "高中",
            "school": "示例高中",
            "address": "浙江省示例市",
            "remark": "",
            "is_key_position": "否",
            "is_internal_auditor": "否",
            "is_regular_employee": "是",
            "is_manager": "否",
            "employment_status": "在职",
            "signature": "张三",
            "probation_end_date": "2024年01月23日",
            "probation_period": "2024年01月15日至2024年01月23日",
        },
        "document": {
            "date": doc_date,
            "year": str(today.year),
            "month": str(today.month),
            "seq_no": "01",
        },
        "training": {
            "course_name": "示例课程",
            "date": "2024年03月01日",
            "period": "2024年03月01日",
            "duration": "1H",
            "duration_hours": "1",
            "instructor_name": "示例讲师",
            "trainer": "示例讲师",
            "location": "会议室",
            "assessment_method": "无",
            "content": "示例培训内容",
            "attendance": "10/10",
            "evaluation": TRAINING_EFFECTIVENESS_EVALUATION,
            "target_audience": "全体员工",
            "year": str(today.year),
            "plan_type": "annual",
            "exam": {
                "first_score": "85",
                "retake_score": "",
                "passed": "是",
                "retrain": "否",
                "score": "85",
                "pass": "是",
                "date": "2024年03月01日",
            },
        },
        "contract": {
            "start_date": "2024年01月15日",
            "end_date": "2027年01月14日",
            "duration_years": "3",
            "type": "固定期限",
        },
        "signature": _build_sample_signature_context(),
        "incentive": incentive,
        "position_safety": {
            "month_label": f"{today.year}年2月",
            "check_date": "2024年01月15日",
            "checker": "张安全员",
            "issues": "无",
            "actions": "无",
            "rectification_notes": "1. 2月8日发现灭火器无铅封，已于2月9日更换完毕。<br>2. 2月15日发现11号警示标识有破损，已于2月16日重新张贴。",
            "inspection_year": str(today.year),
        },
        "row": {"index": "1"},
    }
    from app.services.satisfaction_scoring import (
        build_survey_mark_context,
        generate_respondent_scores,
    )

    ctx["survey"] = build_survey_mark_context(
        generate_respondent_scores(["sample"])["sample"]
    )
    return ctx


def build_sample_list_data(template_id: str = "") -> dict[str, list[dict[str, Any]]]:
    """Return sample list-region data for template preview."""
    from app.core.calendar import WorkCalendar
    from app.models.employee import Employee
    from app.services.hr_generator import (
        TMPL_ROSTER,
        TMPL_SATISFACTION_REPORT,
        TMPL_TRAIN_EVAL,
        build_onboarding_training_list_data,
        build_roster_list_data,
    )
    from app.services.satisfaction_scoring import REPORT_ITEMS

    if template_id == TMPL_SATISFACTION_REPORT:
        return {
            "report_items": [
                {
                    "report": {"item_text": text, "item_score": f"{score:.1f}"},
                    "row": {"index": str(i)},
                }
                for i, (text, score) in enumerate(REPORT_ITEMS, start=1)
            ]
        }

    if template_id == TMPL_ROSTER:
        sample_employees = [
            Employee(
                name="张三（示例）",
                department_name="生产部",
                position_name="操作工",
                hire_date=date(2024, 1, 15),
                gender="男",
                id_no="330102199001011234",
                phone="13812345678",
                education="高中",
                is_key_position=False,
                is_internal_auditor=False,
                is_regular_employee=True,
            ),
            Employee(
                name="李四（示例）",
                department_name="品质部",
                position_name="检验员",
                hire_date=date(2023, 6, 1),
                gender="女",
                id_no="330102198505055678",
                phone="13987654321",
                education="大专",
                is_key_position=False,
                is_internal_auditor=True,
                is_regular_employee=False,
            ),
        ]
        return build_roster_list_data(sample_employees)

    from app.services.training_generator import TMPL_ATTENDANCE, build_attendance_list_data

    if template_id == TMPL_ATTENDANCE:
        sample_employees = [
            Employee(name="张三（示例）", department_name="生产部", position_name="操作工", hire_date=date(2024, 1, 15)),
            Employee(name="李四（示例）", department_name="品质部", position_name="检验员", hire_date=date(2023, 6, 1)),
            Employee(name="王五（示例）", department_name="技术部", position_name="工程师", hire_date=date(2022, 3, 1)),
        ]
        return build_attendance_list_data(sample_employees)

    if template_id != TMPL_TRAIN_EVAL:
        return {}

    emp = Employee(
        name="张三（示例）",
        department_name="生产部",
        position_name="操作工",
        hire_date=date(2024, 1, 15),
    )
    return build_onboarding_training_list_data(
        emp,
        WorkCalendar(),
        "王HR（示例）",
    )
