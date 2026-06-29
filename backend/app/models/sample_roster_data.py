"""Standardized sample roster data for intake template download and testing.

52 employees across four position categories: 生产 / 品质 / 技术 / 管理.
"""
from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.employee import Employee

POSITION_CATEGORIES = ("生产", "品质", "技术", "管理")

SAMPLE_ADDRESS = "浙江省杭州市余杭区良渚街道工矿路88号"


@dataclass(frozen=True)
class SampleEmployee:
    name: str
    department_name: str
    position_name: str
    position_category: str
    hire_date: str
    gender: str
    id_no: str
    phone: str
    education: str
    school: str
    is_key_position: str
    is_internal_auditor: str
    is_regular_employee: str
    is_manager: str
    remark: str = ""

    def to_row(self) -> list[str]:
        return [
            self.name,
            self.department_name,
            self.position_name,
            self.position_category,
            self.hire_date,
            self.gender,
            self.id_no,
            self.phone,
            self.education,
            self.school,
            SAMPLE_ADDRESS,
            self.is_key_position,
            self.is_internal_auditor,
            self.is_regular_employee,
            self.is_manager,
            "在职",
            self.remark,
        ]


def _id(year: int, month: int, day: int, seq: int, *, male: bool) -> str:
    """Build an 18-digit ID compatible with roster ID derivation rules."""
    if male and seq % 2 == 0:
        seq += 1
    if not male and seq % 2 == 1:
        seq += 1
    return f"330106{year:04d}{month:02d}{day:02d}{seq:03d}8"


def _phone(prefix: int, suffix: int) -> str:
    return f"1{prefix}{suffix:08d}"


# fmt: off
SAMPLE_EMPLOYEES: tuple[SampleEmployee, ...] = (
    # ── 管理（6）──────────────────────────────────────────────────────────
    SampleEmployee("陈建国", "综合管理部", "总经理", "管理", "2018-03-01", "男",
                   _id(1975, 6, 12, 11, male=True), _phone(38, 10010001), "本科", "浙江大学",
                   "否", "是", "否", "是", "管理者代表"),
    SampleEmployee("王志强", "综合管理部", "副总经理", "管理", "2019-05-15", "男",
                   _id(1978, 9, 20, 13, male=True), _phone(39, 10010002), "本科", "武汉理工大学",
                   "否", "否", "否", "是"),
    SampleEmployee("刘芳", "综合管理部", "人力资源专员", "管理", "2020-07-01", "女",
                   _id(1992, 3, 8, 22, male=False), _phone(58, 10010003), "大专", "浙江经贸职业技术学院",
                   "否", "否", "否", "否"),
    SampleEmployee("赵敏", "综合管理部", "行政专员", "管理", "2021-02-18", "女",
                   _id(1994, 11, 25, 24, male=False), _phone(37, 10010004), "大专", "杭州职业技术学院",
                   "否", "否", "是", "否"),
    SampleEmployee("周文娟", "综合管理部", "财务主管", "管理", "2019-08-10", "女",
                   _id(1988, 7, 16, 26, male=False), _phone(36, 10010005), "本科", "浙江财经大学",
                   "否", "否", "否", "是"),
    SampleEmployee("孙丽", "综合管理部", "体系专员", "管理", "2020-04-06", "女",
                   _id(1990, 5, 30, 28, male=False), _phone(59, 10010006), "本科", "浙江工业大学",
                   "是", "是", "否", "否", "内审员/文控"),

    # ── 技术（8）──────────────────────────────────────────────────────────
    SampleEmployee("张伟", "技术部", "工艺工程师", "技术", "2019-03-12", "男",
                   _id(1987, 4, 18, 15, male=True), _phone(38, 10020001), "本科", "合肥工业大学",
                   "是", "是", "否", "否", "内审员"),
    SampleEmployee("李娜", "技术部", "工艺工程师", "技术", "2021-06-20", "女",
                   _id(1993, 8, 5, 20, male=False), _phone(39, 10020002), "本科", "南京理工大学",
                   "否", "否", "否", "否"),
    SampleEmployee("杨帆", "技术部", "模具工程师", "技术", "2018-11-08", "男",
                   _id(1986, 12, 3, 17, male=True), _phone(58, 10020003), "本科", "华中科技大学",
                   "是", "否", "否", "否"),
    SampleEmployee("吴建华", "技术部", "模具工程师", "技术", "2020-09-15", "男",
                   _id(1991, 2, 14, 19, male=True), _phone(37, 10020004), "大专", "宁波职业技术学院",
                   "否", "否", "否", "否"),
    SampleEmployee("郑强", "技术部", "设备工程师", "技术", "2019-07-22", "男",
                   _id(1989, 10, 9, 21, male=True), _phone(36, 10020005), "大专", "温州职业技术学院",
                   "否", "否", "否", "否"),
    SampleEmployee("冯磊", "技术部", "设备工程师", "技术", "2022-03-10", "男",
                   _id(1995, 6, 28, 23, male=True), _phone(59, 10020006), "大专", "金华职业技术学院",
                   "否", "否", "否", "否"),
    SampleEmployee("蒋欣", "技术部", "项目工程师", "技术", "2020-01-06", "女",
                   _id(1992, 1, 17, 26, male=False), _phone(38, 10020007), "本科", "同济大学",
                   "否", "否", "否", "否"),
    SampleEmployee("沈涛", "技术部", "生产技术员", "技术", "2023-04-18", "男",
                   _id(1998, 9, 11, 25, male=True), _phone(39, 10020008), "中专", "余杭区技工学校",
                   "否", "否", "是", "否"),

    # ── 品质（10）─────────────────────────────────────────────────────────
    SampleEmployee("马健", "品质部", "品质经理", "品质", "2018-06-01", "男",
                   _id(1983, 5, 22, 11, male=True), _phone(58, 10030001), "本科", "吉林大学",
                   "否", "是", "否", "是", "内审员"),
    SampleEmployee("何丽", "品质部", "检验员", "品质", "2019-09-10", "女",
                   _id(1990, 4, 7, 22, male=False), _phone(37, 10030002), "大专", "浙江机电职业技术学院",
                   "是", "是", "否", "否", "内审员/出货检验"),
    SampleEmployee("许明", "品质部", "检验员", "品质", "2020-11-25", "男",
                   _id(1991, 7, 19, 15, male=True), _phone(36, 10030003), "高中", "余杭第二高级中学",
                   "是", "否", "是", "否", "过程检验"),
    SampleEmployee("曹慧", "品质部", "检验员", "品质", "2021-08-03", "女",
                   _id(1994, 3, 26, 24, male=False), _phone(59, 10030004), "大专", "嘉兴职业技术学院",
                   "否", "否", "是", "否"),
    SampleEmployee("韩冰", "品质部", "检验员", "品质", "2022-05-16", "女",
                   _id(1996, 11, 8, 28, male=False), _phone(38, 10030005), "高中", "良渚高级中学",
                   "否", "否", "是", "否"),
    SampleEmployee("邓超", "品质部", "SQE工程师", "品质", "2019-04-22", "男",
                   _id(1988, 8, 14, 17, male=True), _phone(39, 10030006), "本科", "东南大学",
                   "否", "是", "否", "否", "内审员"),
    SampleEmployee("谢芳", "品质部", "计量管理员", "品质", "2020-10-12", "女",
                   _id(1992, 6, 2, 20, male=False), _phone(58, 10030007), "大专", "浙江计量职业技术学院",
                   "是", "否", "否", "否"),
    SampleEmployee("罗婷", "品质部", "体系工程师", "品质", "2021-01-20", "女",
                   _id(1993, 12, 15, 26, male=False), _phone(37, 10030008), "本科", "浙江工商大学",
                   "否", "是", "否", "否", "内审员"),
    SampleEmployee("唐杰", "品质部", "来料检验员", "品质", "2022-07-08", "男",
                   _id(1997, 4, 21, 19, male=True), _phone(36, 10030009), "中专", "余杭区技工学校",
                   "否", "否", "是", "否"),
    SampleEmployee("梁静", "品质部", "出货检验员", "品质", "2023-02-14", "女",
                   _id(1999, 1, 9, 22, male=False), _phone(59, 10030010), "高中", "余杭第一中学",
                   "否", "否", "是", "否"),

    # ── 生产（28）─────────────────────────────────────────────────────────
    SampleEmployee("徐志刚", "生产部", "生产经理", "生产", "2018-04-01", "男",
                   _id(1982, 3, 5, 13, male=True), _phone(38, 10040001), "大专", "浙江工业职业技术学院",
                   "否", "否", "否", "是"),
    SampleEmployee("胡斌", "生产部", "车间主任", "生产", "2019-02-11", "男",
                   _id(1985, 7, 28, 15, male=True), _phone(39, 10040002), "高中", "余杭第三高级中学",
                   "否", "否", "否", "是"),
    SampleEmployee("朱伟", "生产部", "车间主任", "生产", "2019-06-18", "男",
                   _id(1986, 11, 16, 17, male=True), _phone(58, 10040003), "高中", "良渚高级中学",
                   "否", "否", "否", "是"),
    SampleEmployee("高鹏", "生产部", "班组长", "生产", "2020-03-05", "男",
                   _id(1989, 5, 3, 19, male=True), _phone(37, 10040004), "高中", "余杭第二高级中学",
                   "是", "否", "否", "否", "注塑一线"),
    SampleEmployee("林峰", "生产部", "班组长", "生产", "2020-08-20", "男",
                   _id(1990, 9, 27, 21, male=True), _phone(36, 10040005), "高中", "余杭第一中学",
                   "是", "否", "否", "否", "CNC一线"),
    SampleEmployee("宋洋", "生产部", "班组长", "生产", "2021-04-12", "男",
                   _id(1991, 1, 8, 23, male=True), _phone(59, 10040006), "初中", "良渚中学",
                   "否", "否", "是", "否", "装配一线"),
    SampleEmployee("董强", "生产部", "班组长", "生产", "2021-10-30", "男",
                   _id(1992, 8, 19, 25, male=True), _phone(38, 10040007), "初中", "瓶窑中学",
                   "否", "否", "是", "否", "冲压一线"),
    SampleEmployee("钱勇", "生产部", "操作工", "生产", "2020-05-06", "男",
                   _id(1993, 4, 11, 11, male=True), _phone(39, 10040008), "初中", "良渚中学",
                   "是", "否", "是", "否", "CNC操作"),
    SampleEmployee("孙浩", "生产部", "操作工", "生产", "2020-06-15", "男",
                   _id(1994, 6, 23, 13, male=True), _phone(58, 10040009), "初中", "瓶窑中学",
                   "是", "否", "是", "否", "CNC操作"),
    SampleEmployee("李强", "生产部", "操作工", "生产", "2020-09-01", "男",
                   _id(1995, 2, 7, 15, male=True), _phone(37, 10040010), "初中", "良渚中学",
                   "否", "否", "是", "否", "CNC操作"),
    SampleEmployee("周杰", "生产部", "操作工", "生产", "2021-01-18", "男",
                   _id(1996, 10, 14, 17, male=True), _phone(36, 10040011), "初中", "余杭中学",
                   "否", "否", "是", "否", "CNC操作"),
    SampleEmployee("吴刚", "生产部", "操作工", "生产", "2021-03-22", "男",
                   _id(1997, 7, 30, 19, male=True), _phone(59, 10040012), "初中", "瓶窑中学",
                   "否", "否", "是", "否", "注塑操作"),
    SampleEmployee("郑伟", "生产部", "操作工", "生产", "2021-05-10", "男",
                   _id(1998, 3, 18, 21, male=True), _phone(38, 10040013), "初中", "良渚中学",
                   "是", "否", "是", "否", "注塑操作"),
    SampleEmployee("王磊", "生产部", "操作工", "生产", "2021-07-28", "男",
                   _id(1999, 8, 6, 23, male=True), _phone(39, 10040014), "初中", "余杭中学",
                   "否", "否", "是", "否", "注塑操作"),
    SampleEmployee("冯军", "生产部", "操作工", "生产", "2021-11-05", "男",
                   _id(2000, 1, 22, 25, male=True), _phone(58, 10040015), "初中", "瓶窑中学",
                   "否", "否", "是", "否", "注塑操作"),
    SampleEmployee("陈明", "生产部", "操作工", "生产", "2022-02-14", "男",
                   _id(2001, 5, 9, 27, male=True), _phone(37, 10040016), "初中", "良渚中学",
                   "否", "否", "是", "否", "装配操作"),
    SampleEmployee("褚亮", "生产部", "操作工", "生产", "2022-04-20", "男",
                   _id(2002, 11, 3, 29, male=True), _phone(36, 10040017), "初中", "余杭中学",
                   "否", "否", "是", "否", "装配操作"),
    SampleEmployee("卫华", "生产部", "操作工", "生产", "2022-06-08", "男",
                   _id(2003, 4, 16, 31, male=True), _phone(59, 10040018), "初中", "瓶窑中学",
                   "否", "否", "是", "否", "装配操作"),
    SampleEmployee("蒋平", "生产部", "操作工", "生产", "2022-08-25", "男",
                   _id(2004, 9, 28, 33, male=True), _phone(38, 10040019), "初中", "良渚中学",
                   "否", "否", "是", "否", "装配操作"),
    SampleEmployee("沈龙", "生产部", "操作工", "生产", "2022-10-11", "男",
                   _id(2005, 12, 5, 35, male=True), _phone(39, 10040020), "初中", "余杭中学",
                   "否", "否", "是", "否", "冲压操作"),
    SampleEmployee("韩东", "生产部", "操作工", "生产", "2023-01-06", "男",
                   _id(2006, 6, 19, 37, male=True), _phone(58, 10040021), "初中", "瓶窑中学",
                   "是", "否", "是", "否", "冲压操作"),
    SampleEmployee("杨波", "生产部", "操作工", "生产", "2023-03-15", "男",
                   _id(2007, 2, 24, 39, male=True), _phone(37, 10040022), "初中", "良渚中学",
                   "否", "否", "是", "否", "冲压操作"),
    SampleEmployee("朱亮", "生产部", "操作工", "生产", "2023-05-20", "男",
                   _id(2008, 8, 11, 41, male=True), _phone(36, 10040023), "初中", "余杭中学",
                   "否", "否", "是", "否", "焊接操作"),
    SampleEmployee("秦勇", "生产部", "操作工", "生产", "2023-07-10", "男",
                   _id(2009, 3, 7, 43, male=True), _phone(59, 10040024), "初中", "瓶窑中学",
                   "是", "否", "是", "否", "焊接操作"),
    SampleEmployee("尤刚", "生产部", "操作工", "生产", "2023-09-01", "男",
                   _id(2010, 7, 15, 45, male=True), _phone(38, 10040025), "初中", "良渚中学",
                   "否", "否", "是", "否", "焊接操作"),
    SampleEmployee("许涛", "生产部", "操作工", "生产", "2023-11-18", "男",
                   _id(2011, 10, 29, 47, male=True), _phone(39, 10040026), "初中", "余杭中学",
                   "否", "否", "是", "否", "去毛刺"),
    SampleEmployee("何斌", "生产部", "操作工", "生产", "2024-01-08", "男",
                   _id(2012, 5, 13, 49, male=True), _phone(58, 10040027), "初中", "瓶窑中学",
                   "否", "否", "是", "否", "包装操作"),
    SampleEmployee("吕超", "生产部", "操作工", "生产", "2024-03-12", "男",
                   _id(2013, 9, 21, 51, male=True), _phone(37, 10040028), "初中", "良渚中学",
                   "否", "否", "是", "否", "包装操作"),
)
# fmt: on


def get_sample_roster_rows() -> list[list[str]]:
    """Return roster rows for Excel template (one list per employee)."""
    return [emp.to_row() for emp in SAMPLE_EMPLOYEES]


def get_sample_roster_summary() -> dict[str, int]:
    """Return headcount by position_category."""
    summary: dict[str, int] = {cat: 0 for cat in POSITION_CATEGORIES}
    for emp in SAMPLE_EMPLOYEES:
        summary[emp.position_category] += 1
    return summary


def sample_employees_as_models() -> list["Employee"]:
    """Convert sample roster rows into Employee models for tests and previews."""
    from datetime import date

    from app.models.employee import Employee, _parse_date_cell

    employees: list[Employee] = []
    for sample in SAMPLE_EMPLOYEES:
        hire = _parse_date_cell(sample.hire_date) or date.today()
        employees.append(
            Employee(
                name=sample.name,
                department_name=sample.department_name,
                position_name=sample.position_name,
                position_category=sample.position_category,
                hire_date=hire,
                gender=sample.gender,
                id_no=sample.id_no,
                phone=sample.phone,
                education=sample.education,
                school=sample.school,
                is_key_position=sample.is_key_position == "是",
                is_internal_auditor=sample.is_internal_auditor == "是",
                is_regular_employee=sample.is_regular_employee == "是",
                is_manager=sample.is_manager == "是",
                employment_status="在职",
                remark=sample.remark,
            )
        )
    return employees
