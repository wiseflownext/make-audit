## Context

入职岗位培训评价表包含 4 条固定培训项目，明细列需与花名册、工作日历联动。综管部负责企业文化/制度/环境类培训，培训人应从花名册综管部人员中解析。

## Goals / Non-Goals

**Goals:**
- 生成时自动填充 4 行培训明细
- 培训日期按入职后第 N 个工作日排算（N=1..4）
- 培训人从花名册综管部解析，支持 `manager_map.hr_manager` 覆盖

**Non-Goals:**
- 不改动第 5～8 空行的模版结构
- 不引入可配置的培训结论/合格标准（固定「合格」「是」）
- 第 4 行岗位培训仍由综管部填写（不改为任职部门负责人）

## Decisions

### 1. 新增 `onboarding.*` 命名空间 + LIST 循环区

模版四条培训行改为 `<!-- LIST:onboarding_training_rows -->`，与现有 `training_rows` 模式一致。

**备选：** 在 HTML 中写死 4 组 `{{onboarding.date_1}}` 等占位符 — 否决，扩展性差且与 LIST 约定不一致。

### 2. 工作日推算规则

使用 `WorkCalendar.add_working_days(hire_date, index)`，其中 index=0..3 对应第 1～4 个工作日。

- index=0：入职当天（若为工作日）或下一个工作日
- index=1：入职后第 2 个工作日

与现有日历模块、转正日期推算保持一致。

### 3. 综管部培训人解析

从花名册筛选部门名含「综管部/综合管理部/行政管理部」的在职员工，优先级：
1. `is_manager=True`
2. 岗位名含「主管/经理/负责人」
3. 第一条综管部记录

解析结果写入 `manager_map.hr_manager`（可被 API 显式传入覆盖）。

### 4. 预览数据

`build_sample_list_data()` 在培训评价表预览时注入示例 4 行，与 `build_sample_context()` 分离，避免污染其它模版预览。

## Risks / Trade-offs

- **[花名册无综管部人员]** → 培训人/签名为空，预检高亮缺失项；审核老师可手动传 `manager_map`
- **[部门命名不一致]** → 关键字匹配可能漏检；后续可扩展企业级部门别名配置

## Migration Plan

无数据迁移。部署后重新生成资料包即可得到填充后的培训评价表。

## Open Questions

- 第 4 行岗位培训是否应改为任职部门负责人 — 当前按「综管部负责」统一处理
