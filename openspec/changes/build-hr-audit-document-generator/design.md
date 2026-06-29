## Context

仓库当前是一个「模版与规格资产库」：`template/人力资源/**` 下每个表单都带 `template.html` + `meta.yaml`（声明 `generation_granularity`、`data_sources`、`variables`、`output_naming`），`json文件/training-plan-comprehensive.json` 提供新员工与年度培训计划数据。尚无 Web/后端应用代码。

本变更要在此资产之上构建一个面向审核老师的 Web 系统：上传真实员工花名册与可选签名后，按体系规则自动生成整套人力资源审核资料包并打包下载。关键约束：

- 模版数据驱动，已有 `meta.yaml` 应作为生成引擎的配置来源。
- 占位符统一为 `{{namespace.key}}`，员工主数据需覆盖所有 `{{employee.*}}`。
- 日期需真实合法（单休 + 日历），用户不关心内部算法。
- 签名可选，不阻塞生成。
- 处理真实个人信息，需考虑授权与可追溯。

## Goals / Non-Goals

**Goals:**
- 以现有 `template/人力资源/**` 的 `meta.yaml` 为配置，构建可扩展的模版渲染 + 生成引擎。
- 提供上传页、下载页、模版管理页三个核心界面。
- 实现入职/转正/满意度档案规则、培训计划与签到记录、个人培训记录表（一人一年一份）。
- 实现培训「面向对象 → 员工集合」匹配映射，并保证签到表与个人培训记录互相一致。
- 实现单休 + 日历的真实工作日推算。
- 签名可选与抠底处理；管理人员签名同规则回退。

**Non-Goals:**
- 不在本期覆盖人力资源以外的体系域（如生产、采购、设备）。
- 不做多租户计费、权限分级等企业级账户体系（先单用户/审核老师工作台）。
- 不追求自动 OCR 花名册图片，本期花名册以结构化 Excel/CSV 为输入。
- 不实现真实电子签名法律存证，仅做视觉电子签名。

## Decisions

### 决策 1：模版渲染采用 HTML 占位符替换 + 打印级 CSS，输出 PDF
- 现有模版即 A4 打印级 HTML（`@page`/`@media print`），天然适合占位符替换后转 PDF。
- 选择 `{{namespace.key}}` 字符串替换 + 列表区循环渲染（如签到行、培训行）。
- 备选：用 Word/Excel 模板引擎。否决原因：现有资产是 HTML，迁移成本高且版式已调好。

### 决策 2：以 `meta.yaml` 作为单一生成配置来源
- `generation_granularity`（per_employee / per_employee_per_year / per_year / per_enterprise 等）直接驱动生成循环维度。
- `data_sources`、`variables`、`output_naming`、`signature_mappings`、`date_mappings`、`checkbox_mappings` 提供绑定与命名。
- 备选：另建独立配置。否决原因：会与现有 `meta.yaml` 重复且易不一致。

### 决策 3：数据命名空间与员工主数据模型
- 命名空间：`enterprise`、`employee`、`contract`、`training`（含 `training.exam`）、`signature`、`document`、`incentive`、`position_safety`。
- 员工主数据字段集合统一为：name、department_name、position_name、position_category、gender、id_no、birth_date、hire_date、phone、education、school、address、remark、is_key_position、is_internal_auditor、is_regular_employee、is_manager、employment_status。
- 花名册未提供的派生字段（出生年月、性别）从身份证号推导。

### 决策 4：培训「面向对象 → 员工」用显式映射表 + 规则解析
- 维护「面向对象」到匹配规则的映射（全体员工 / 部门定向 / 岗位定向 / 内审员 / 管理人员 / 新进员工等）。
- 培训日期排定后，生成「场次」对象；签到记录与个人培训记录均从同一场次集合派生，保证一致性。
- 备选：自然语言模糊匹配。否决原因：不可控、不可测，审核场景要求确定性。

### 决策 5：工作日历能力独立成模块
- 输入：起始日期、偏移天数/区间、单休规则、节假日表；输出：合法工作日。
- 服务于转正日期、入职后第 N 天培训、年度培训计划排期。
- 单休默认周日休息，可配置；法定节假日可后续接入。

### 决策 6：签名处理与可选回退
- 上传签名照片 → 抠底为透明 PNG → 绑定 `employee.signature`。
- 未上传 → 渲染非打印体（手写风格字体）文本签名。
- 管理人员签名（`signature.*`）同规则。

### 决策 7：技术栈
- 后端 Python（FastAPI）：解析 Excel/CSV、规则引擎、HTML 渲染、PDF 转换、ZIP 打包。
- 前端：现代 Web UI（上传页 / 下载页 / 模版管理页 + 预览）。
- 选 Python 因花名册解析（openpyxl/pandas）、图像抠底（Pillow/rembg）、HTML→PDF（playwright/weasyprint）生态成熟。

## Risks / Trade-offs

- [HTML→PDF 中文字体与分页] → 固定 SimSun 等中文字体，沿用现有打印 CSS，生成后抽样校验分页。
- [花名册列名不统一] → 提供列映射/模板下载，解析阶段做列名归一与必填校验。
- [签名抠底质量参差] → 提供阈值参数与预览确认，未上传时回退文本签名。
- [培训面向对象表述多样] → 映射表 + 未命中清单，未命中项提示人工归类，不静默丢弃。
- [真实个人信息合规] → 数据仅用于本次生成，提供生成依据/可追溯标识；不做超出授权的留存。
- [日期排算与真实业务偏差] → 工作日历可配置，转正/培训日期生成后允许人工微调。

## Migration Plan

- 全新增量，无存量系统迁移。
- 分阶段：先打通「花名册上传 → 单员工档案生成 → 预览」最小闭环，再接入培训联动与 ZIP 打包，最后补模版管理在线编辑。
- 回滚：各能力独立，可按能力关闭，不影响既有模版资产。

## Open Questions

- 年度覆盖范围（近三年）的「当前年」以系统时间还是用户指定为准？
- 节假日/调休日历是否需要接入官方数据源，还是仅单休？
- 模版在线编辑保存是覆盖内置模版，还是按客户存独立版本（建议按客户分版本）？
- 个人培训记录表是否需纳入新员工入司 6 门培训，还是仅年度培训？
