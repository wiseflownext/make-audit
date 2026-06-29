"""Enterprise basic info model and Excel parsing utilities."""
from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FIELDS: tuple[str, ...] = ("name",)

FIELD_ALIASES: dict[str, str] = {
    "企业名称": "name",
    "企业名称*": "name",
    "name": "name",
    "企业简称": "short_name",
    "short_name": "short_name",
    "法定代表人": "legal_rep",
    "legal_rep": "legal_rep",
    "联系人": "contact",
    "contact": "contact",
    "联系电话": "phone",
    "电话": "phone",
    "phone": "phone",
    "企业地址": "address",
    "地址": "address",
    "address": "address",
    "审核年度": "year",
    "年度": "year",
    "year": "year",
}

CANONICAL_KEYS = frozenset(FIELD_ALIASES.values())


class EnterpriseValidationError(ValueError):
    """Raised when the uploaded enterprise file fails validation."""


def _clean_label(raw: Any) -> str:
    return str(raw).strip().rstrip("*").strip()


def _canonical_key(label: str) -> str | None:
    if not label:
        return None
    direct = FIELD_ALIASES.get(label) or FIELD_ALIASES.get(label.lower())
    if direct:
        return direct
    cleaned = _clean_label(label)
    return FIELD_ALIASES.get(cleaned) or FIELD_ALIASES.get(cleaned.lower())


def _read_dataframe(source: bytes, filename: str, sheet_name: str | None = None) -> pd.DataFrame:
    ext = Path(filename).suffix.lower() if filename else ""
    buf = BytesIO(source)
    read_kwargs: dict = {"dtype": str, "keep_default_na": False}
    if sheet_name:
        read_kwargs["sheet_name"] = sheet_name

    def _load_excel() -> pd.DataFrame:
        raw = pd.read_excel(buf, header=None, **read_kwargs)
        for idx in range(min(len(raw), 10)):
            row = raw.iloc[idx]
            if any(str(v).strip() in ("字段", "field", "Field") for v in row):
                header = [str(v).strip() for v in row.tolist()]
                df = raw.iloc[idx + 1 :].copy()
                df.columns = header
                return df.reset_index(drop=True)
        buf.seek(0)
        return pd.read_excel(buf, **read_kwargs)

    if ext in (".xlsx", ".xls", ".xlsm") or not ext:
        try:
            return _load_excel()
        except Exception:
            buf.seek(0)
            return pd.read_csv(buf, dtype=str, keep_default_na=False)
    if ext == ".csv":
        return pd.read_csv(buf, dtype=str, keep_default_na=False)
    try:
        return _load_excel()
    except Exception:
        buf.seek(0)
        return pd.read_csv(buf, dtype=str, keep_default_na=False)


def _detect_key_value_columns(df: pd.DataFrame) -> tuple[str, str]:
    cols = [str(c).strip() for c in df.columns]
    for field_header, value_header in (("字段", "值"), ("field", "value"), ("Field", "Value")):
        if field_header in cols and value_header in cols:
            return field_header, value_header
    if len(df.columns) >= 2:
        return df.columns[0], df.columns[1]
    raise EnterpriseValidationError("企业资料文件格式不正确，需要「字段」与「值」两列。")


def _parse_key_value(df: pd.DataFrame) -> dict[str, str]:
    field_col, value_col = _detect_key_value_columns(df)
    result: dict[str, str] = {}

    for _, row in df.iterrows():
        label = _clean_label(row.get(field_col, ""))
        if not label or label in ("字段", "field", "Field"):
            continue
        key = _canonical_key(label)
        if not key:
            continue
        value = str(row.get(value_col, "")).strip()
        result[key] = value

    return result


def _parse_horizontal(df: pd.DataFrame) -> dict[str, str]:
    """Fallback: first row headers, second row values."""
    if len(df) < 1:
        return {}
    header_row = df.iloc[0]
    value_row = df.iloc[1] if len(df) > 1 else df.iloc[0]
    result: dict[str, str] = {}
    for col in df.columns:
        key = _canonical_key(_clean_label(col))
        if not key:
            key = _canonical_key(_clean_label(header_row.get(col, "")))
        if key:
            raw = value_row.get(col, "")
            result[key] = str(raw).strip()
    return result


def parse_enterprise(
    source: bytes | Path,
    filename: str = "",
    sheet_name: str | None = None,
) -> dict[str, str]:
    """Parse an Excel or CSV enterprise info file.

    Raises :class:`EnterpriseValidationError` on missing required fields.
    """
    if isinstance(source, Path):
        raw_bytes = source.read_bytes()
        fname = source.name
    else:
        raw_bytes = source
        fname = filename

    df = _read_dataframe(raw_bytes, fname, sheet_name=sheet_name)

    if df.empty:
        raise EnterpriseValidationError("企业资料文件为空。")

    cols = {_clean_label(c) for c in df.columns}
    if "字段" in cols or cols.intersection({"field", "Field"}) or len(df.columns) == 2:
        data = _parse_key_value(df)
    else:
        data = _parse_horizontal(df)

    if not data.get("name"):
        raise EnterpriseValidationError("企业资料缺少必填字段：企业名称。")

    result = {key: data.get(key, "") for key in CANONICAL_KEYS}
    if not result.get("year"):
        result["year"] = str(date.today().year)
    return result
