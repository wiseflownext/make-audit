## Why

当前企业基础资料需在 Web 表单中逐字段手工填写，与花名册已支持的 Excel 上传方式不一致，审核老师需要在两种录入模式间切换，效率低且易出错。企业资料字段少、结构固定，适合与花名册一样通过 Excel 模板一次性导入。

## What Changes

- 移除上传资料页的企业资料手工表单，改为 Excel 上传（含模板下载）
- 新增企业资料 Excel 模板生成与解析逻辑（键值对格式：字段名 + 值）
- 新增 `POST /intake/enterprise` 文件上传接口，替换原 JSON 保存接口
- 保留 `GET /intake/enterprise` 供前端展示已上传的企业资料摘要
- 生成前校验逻辑不变：缺少企业名称仍阻止生成

## Capabilities

### New Capabilities

（无新增能力域，在既有 client-data-intake 内扩展）

### Modified Capabilities

- `client-data-intake`: 企业基础资料录入方式由 Web 表单改为 Excel 上传；新增模板下载与解析校验场景

## Impact

- 后端：`backend/app/api/intake.py`、`backend/app/models/`（新增 enterprise 解析与模板模块）
- 前端：`frontend/src/pages/UploadPage.tsx`（EnterpriseForm → EnterpriseUpload）
- 测试：新增 enterprise 解析单元测试
- **BREAKING**: 移除 `POST /intake/enterprise` JSON 请求体接口，改为 multipart 文件上传
