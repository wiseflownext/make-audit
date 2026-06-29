"""Employee master data model and roster parsing utilities.

Covers tasks 3.1 – 3.5:
  3.1  Employee dataclass with all canonical fields
  3.2  Excel/CSV roster parsing with column-name normalisation
  3.3  Required-column validation with clear error messages
  3.4  Birth date & gender derivation from Chinese national ID
  3.5  Boolean flag parsing (key position / internal auditor / regular / manager)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# 3.1 Employee model
# ---------------------------------------------------------------------------


@dataclass
class Employee:
    name: str
    department_name: str
    position_name: str
    hire_date: date

    # Optional enrichment fields
    position_category: str = ""
    gender: str = ""          # "男" / "女"
    id_no: str = ""
    birth_date: date | None = None
    phone: str = ""
    education: str = ""
    school: str = ""
    address: str = ""
    remark: str = ""
    employment_status: str = "在职"

    # Boolean flags
    is_key_position: bool = False
    is_internal_auditor: bool = False
    is_regular_employee: bool = True   # 普通员工（试用期 7 天）
    is_manager: bool = False

    # Derived / computed
    probation_end_date: date | None = None  # filled by calendar module
    signature: str = ""                     # base64 img or text fallback

    def to_namespace_dict(self) -> dict[str, Any]:
        """Return a flat dict keyed by ``employee.<field>`` values."""
        return {
            "name": self.name,
            "department_name": self.department_name,
            "position_name": self.position_name,
            "position_category": self.position_category,
            "gender": self.gender,
            "id_no": self.id_no,
            "birth_date": _fmt_date(self.birth_date),
            "hire_date": _fmt_date(self.hire_date),
            "phone": self.phone,
            "education": self.education,
            "school": self.school,
            "address": self.address,
            "remark": self.remark,
            "is_key_position": "是" if self.is_key_position else "否",
            "is_internal_auditor": "是" if self.is_internal_auditor else "否",
            "is_regular_employee": "是" if self.is_regular_employee else "否",
            "is_manager": "是" if self.is_manager else "否",
            "employment_status": self.employment_status,
            "probation_end_date": _fmt_date(self.probation_end_date),
            "signature": self.signature,
        }


def _fmt_date(d: date | None) -> str:
    if d is None:
        return ""
    return d.strftime("%Y年%m月%d日")


# ---------------------------------------------------------------------------
# 3.3 Validation helpers
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS: tuple[str, ...] = ("name", "department_name", "position_name", "hire_date")

# 3.2  Column name normalisation map (Chinese synonyms → canonical field name)
COLUMN_ALIASES: dict[str, str] = {
    # name
    "姓名": "name",
    "员工姓名": "name",
    "name": "name",
    # department
    "部门": "department_name",
    "所属部门": "department_name",
    "department": "department_name",
    "department_name": "department_name",
    # position
    "岗位": "position_name",
    "职位": "position_name",
    "岗位名称": "position_name",
    "position": "position_name",
    "position_name": "position_name",
    # position category
    "岗位类别": "position_category",
    "职位类别": "position_category",
    "position_category": "position_category",
    # hire date
    "入职日期": "hire_date",
    "入职时间": "hire_date",
    "hire_date": "hire_date",
    "入职": "hire_date",
    # gender
    "性别": "gender",
    "gender": "gender",
    # id number
    "身份证": "id_no",
    "身份证号": "id_no",
    "身份证号码": "id_no",
    "id_no": "id_no",
    # birth date
    "出生年月": "birth_date",
    "出生日期": "birth_date",
    "birth_date": "birth_date",
    # phone
    "联系电话": "phone",
    "手机": "phone",
    "电话": "phone",
    "phone": "phone",
    # education
    "学历": "education",
    "education": "education",
    # school
    "毕业院校": "school",
    "学校": "school",
    "school": "school",
    # address
    "家庭住址": "address",
    "地址": "address",
    "address": "address",
    # remark
    "备注": "remark",
    "remark": "remark",
    # employment status
    "在职状态": "employment_status",
    "employment_status": "employment_status",
    # boolean flags
    "是否重点岗位": "is_key_position",
    "重点岗位": "is_key_position",
    "is_key_position": "is_key_position",
    "是否内审员": "is_internal_auditor",
    "内审员": "is_internal_auditor",
    "is_internal_auditor": "is_internal_auditor",
    "是否普通员工": "is_regular_employee",
    "普通员工": "is_regular_employee",
    "is_regular_employee": "is_regular_employee",
    "是否管理人员": "is_manager",
    "管理人员": "is_manager",
    "is_manager": "is_manager",
}


class RosterValidationError(ValueError):
    """Raised when the uploaded roster file fails validation."""


# ---------------------------------------------------------------------------
# 3.4 ID card derivation
# ---------------------------------------------------------------------------

_ID_RE = re.compile(r"^\d{17}[\dXx]$")


def derive_from_id(id_no: str) -> tuple[date | None, str]:
    """Return ``(birth_date, gender)`` derived from a Chinese national ID.

    Returns ``(None, "")`` when *id_no* is blank or malformed.
    """
    if not id_no or not _ID_RE.match(id_no.strip()):
        return None, ""
    clean = id_no.strip()
    try:
        year = int(clean[6:10])
        month = int(clean[10:12])
        day = int(clean[12:14])
        birth = date(year, month, day)
    except ValueError:
        return None, ""
    gender = "男" if int(clean[16]) % 2 == 1 else "女"
    return birth, gender


# ---------------------------------------------------------------------------
# 3.5 Boolean flag parsing
# ---------------------------------------------------------------------------

_TRUE_VALUES = frozenset({"是", "yes", "true", "1", "y", "✓", "√"})
_FALSE_VALUES = frozenset({"否", "no", "false", "0", "n"})


def parse_bool(raw: Any, default: bool = False) -> bool:
    """Convert a raw cell value to bool using Chinese/English conventions."""
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    if isinstance(raw, str):
        cleaned = raw.strip().lower()
        if cleaned in _TRUE_VALUES:
            return True
        if cleaned in _FALSE_VALUES:
            return False
    return default


# ---------------------------------------------------------------------------
# 3.2 Roster parsing (Excel / CSV)
# ---------------------------------------------------------------------------


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename dataframe columns using COLUMN_ALIASES, lower-strip first."""
    rename_map: dict[str, str] = {}
    for col in df.columns:
        normalised = str(col).strip().rstrip("*").strip()
        canonical = COLUMN_ALIASES.get(normalised) or COLUMN_ALIASES.get(normalised.lower())
        if not canonical:
            canonical = COLUMN_ALIASES.get(str(col).strip()) or COLUMN_ALIASES.get(str(col).strip().lower())
        if canonical:
            rename_map[col] = canonical
    return df.rename(columns=rename_map)


def _parse_date_cell(raw: Any) -> date | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    if isinstance(raw, date):
        return raw
    if hasattr(raw, "date"):
        return raw.date()
    try:
        parsed = pd.to_datetime(str(raw), dayfirst=False, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


def _read_roster_dataframe(buf: BytesIO, sheet_name: str | None = None) -> pd.DataFrame:
    read_kwargs: dict = {"dtype": str, "keep_default_na": False}
    if sheet_name:
        read_kwargs["sheet_name"] = sheet_name

    raw = pd.read_excel(buf, header=None, **read_kwargs)
    for idx in range(min(len(raw), 10)):
        row = raw.iloc[idx]
        if any("姓名" in str(v) for v in row):
            header = [str(v).strip() for v in row.tolist()]
            df = raw.iloc[idx + 1 :].copy()
            df.columns = header
            return df.reset_index(drop=True)

    buf.seek(0)
    return pd.read_excel(buf, **read_kwargs)


def parse_roster(
    source: bytes | Path,
    filename: str = "",
    sheet_name: str | None = None,
) -> list[Employee]:
    """Parse an Excel or CSV roster file and return a list of :class:`Employee`.

    Raises :class:`RosterValidationError` on missing required columns or
    completely empty file.
    """
    fname = filename or (source.name if isinstance(source, Path) else "")
    ext = Path(fname).suffix.lower() if fname else ""

    if isinstance(source, Path):
        raw_bytes = source.read_bytes()
        ext = source.suffix.lower()
    else:
        raw_bytes = source

    buf = BytesIO(raw_bytes)

    if ext in (".xlsx", ".xls", ".xlsm"):
        df = _read_roster_dataframe(buf, sheet_name=sheet_name)
    elif ext == ".csv":
        df = pd.read_csv(buf, dtype=str, keep_default_na=False)
    else:
        try:
            df = _read_roster_dataframe(buf, sheet_name=sheet_name)
        except Exception:
            buf.seek(0)
            df = pd.read_csv(buf, dtype=str, keep_default_na=False)

    df = _normalise_columns(df)

    # 3.3 Required column validation
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RosterValidationError(
            f"花名册缺少必需列: {', '.join(missing)}。"
            f"请确保文件包含以下列: {', '.join(REQUIRED_COLUMNS)}"
        )

    if df.empty:
        raise RosterValidationError("花名册文件为空，未解析到任何员工记录。")

    employees: list[Employee] = []
    for idx, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue  # skip blank rows

        hire_raw = row.get("hire_date", "")
        hire = _parse_date_cell(hire_raw)
        if hire is None:
            raise RosterValidationError(
                f"第 {idx + 2} 行员工「{name}」的入职日期无法解析: {hire_raw!r}"
            )

        id_no = str(row.get("id_no", "")).strip()
        birth_raw = row.get("birth_date", "")
        birth = _parse_date_cell(birth_raw)
        gender = str(row.get("gender", "")).strip()

        # 3.4 Derive from ID card when fields are missing
        if id_no:
            derived_birth, derived_gender = derive_from_id(id_no)
            if birth is None and derived_birth:
                birth = derived_birth
            if not gender and derived_gender:
                gender = derived_gender

        emp = Employee(
            name=name,
            department_name=str(row.get("department_name", "")).strip(),
            position_name=str(row.get("position_name", "")).strip(),
            hire_date=hire,
            position_category=str(row.get("position_category", "")).strip(),
            gender=gender,
            id_no=id_no,
            birth_date=birth,
            phone=str(row.get("phone", "")).strip(),
            education=str(row.get("education", "")).strip(),
            school=str(row.get("school", "")).strip(),
            address=str(row.get("address", "")).strip(),
            remark=str(row.get("remark", "")).strip(),
            employment_status=str(row.get("employment_status", "在职")).strip() or "在职",
            # 3.5 Boolean flag parsing
            is_key_position=parse_bool(row.get("is_key_position", ""), default=False),
            is_internal_auditor=parse_bool(row.get("is_internal_auditor", ""), default=False),
            is_regular_employee=parse_bool(row.get("is_regular_employee", ""), default=True),
            is_manager=parse_bool(row.get("is_manager", ""), default=False),
        )
        employees.append(emp)

    return employees
