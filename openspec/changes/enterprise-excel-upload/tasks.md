## 1. 后端模型与模板

- [x] 1.1 新增 `enterprise_template.py`：生成键值对 Excel 模板（含字段说明行）
- [x] 1.2 新增 `enterprise.py`：解析 Excel/CSV 键值对，校验企业名称必填，返回 canonical dict
- [x] 1.3 新增 `test_enterprise.py`：覆盖成功解析、缺少必填字段、未知字段忽略

## 2. 后端 API

- [x] 2.1 新增 `GET /intake/enterprise/template` 下载模板
- [x] 2.2 将 `POST /intake/enterprise` 改为 multipart 文件上传，调用 `parse_enterprise`
- [x] 2.3 更新 `generate.py` 错误提示文案（「上传」替代「填写」）

## 3. 前端

- [x] 3.1 将 `EnterpriseForm` 替换为 `EnterpriseUpload`（下载模板 + 上传 + 摘要展示）
- [x] 3.2 移除手工表单，更新就绪提示逻辑

## 4. 验证

- [x] 4.1 运行后端测试确保 enterprise 解析通过
