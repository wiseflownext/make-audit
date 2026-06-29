## Why

新员工入职岗位培训评价表中的培训明细行（培训时间、培训部门、培训人、培训结论、是否满足上岗要求）目前为空白占位，生成后仍需审核老师手工补填，与系统「按花名册与规则自动出档」的目标不一致。

## What Changes

- 为「4新员工入职岗位培训评价表」四条固定培训项目自动填充明细字段
- 培训时间按入职日期推算：第 1～4 个工作日（入职当天若为工作日则计为第 1 个工作日）
- 培训部门默认「综管部」；培训人从花名册综管部人员中解析（优先管理人员/主管）
- 培训结论默认「合格」，是否满足上岗要求默认「是」
- 模版 HTML 改为 LIST 循环区，新增 `onboarding.*` 命名空间
- 未显式传入 `manager_map.hr_manager` 时，从花名册自动解析综管部负责人

## Capabilities

### New Capabilities

（无新增能力域）

### Modified Capabilities

- `hr-document-generation`: 转正类档案中的入职岗位培训评价表 MUST 自动填充培训明细行及综管部培训人

## Impact

- 模版：`template/人力资源/4新员工入职岗位培训评价表/template.html`、`meta.yaml`
- 后端：`backend/app/services/hr_generator.py`、`backend/app/core/namespaces.py`、`backend/app/services/sample_context.py`
- 预览 API：`backend/app/api/templates.py`
- 生成 API：`backend/app/api/generate.py`（传入完整花名册用于解析综管部负责人）
- 测试：新增 `backend/tests/test_hr_generator.py`
