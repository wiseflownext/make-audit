## Context

花名册已采用「下载模板 → 填写 → 上传解析」流程（`roster_template.py` + `parse_roster`）。企业资料为单条记录、字段固定（`ENTERPRISE_KEYS`），适合键值对 Excel 模板而非多行表格。

## Goals / Non-Goals

**Goals:**
- 企业资料与花名册录入体验一致（模板下载 + Excel 上传）
- 复用现有 pandas/openpyxl 依赖与 intake API 模式
- 上传后展示已解析的企业资料摘要供确认

**Non-Goals:**
- 不支持 CSV（企业字段少，Excel 模板足够）
- 不保留 JSON 表单保存接口
- 不做 OCR 或非结构化文档解析

## Decisions

### 1. Excel 模板格式：键值对（两列）

| 字段 | 值 |
|------|-----|
| 企业名称* | （用户填写） |
| 企业简称 | |
| ... | |

- **理由**：单条记录用纵向键值对比横向宽表更直观，审核老师不易填错列
- **备选**：与花名册相同的多列单行表 — 字段名作为表头 —  rejected，键值对更符合「资料表」习惯

### 2. 解析模块

- 新增 `backend/app/models/enterprise.py`：`parse_enterprise()` + `EnterpriseValidationError`
- 新增 `backend/app/models/enterprise_template.py`：`generate_enterprise_template()`
- 列名别名映射复用与花名册相同的 normalisation 思路（中文标签 → canonical key）

### 3. API 变更

| 方法 | 路径 | 行为 |
|------|------|------|
| GET | `/intake/enterprise/template` | 下载模板（新增） |
| POST | `/intake/enterprise` | multipart 文件上传（替换原 JSON） |
| GET | `/intake/enterprise` | 不变，返回已解析数据 |

### 4. 前端

- `EnterpriseForm` 替换为 `EnterpriseUpload`，UI 对齐 `RosterUpload`（下载模板 + 上传按钮）
- 上传成功后展示企业资料摘要（名称、简称、年度等）
- 移除所有 `<input>` 手工字段

## Risks / Trade-offs

- **Breaking API**：若有外部调用 JSON POST，需改用文件上传 → 当前为单用户工作台，影响可接受
- **模板格式误用**：用户可能删除字段行 → 解析时校验必填字段并给出中文错误提示

## Migration Plan

1. 部署新 API 与前端
2. 审核老师改用模板填写，无需数据迁移（内存会话）

## Open Questions

（无）
