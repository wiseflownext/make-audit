## ADDED Requirements

### Requirement: 内置模版库浏览
系统 SHALL 内置全部人力资源表单模版，并提供按分类浏览的模版管理界面。每个模版 MUST 包含 HTML 版式、`meta.yaml` 元数据与占位符定义。

#### Scenario: 浏览模版列表
- **WHEN** 审核老师打开模版管理页
- **THEN** 系统按分类列出全部内置模版及其标题、生成粒度与状态

### Requirement: 模版在线编辑与保存
系统 SHALL 允许在模版管理界面直接修改模版内容并保存，以支持模版迭代或针对不同客户的定制。

#### Scenario: 编辑并保存模版
- **WHEN** 审核老师修改某模版的 HTML 或字段并点击保存
- **THEN** 系统持久化修改后的模版版本，后续生成使用最新模版

#### Scenario: 保存非法占位符提示
- **WHEN** 保存的模版中包含未闭合或非 `{{namespace.key}}` 规范的占位符
- **THEN** 系统提示占位符语法错误并指出位置，例如 `{position_safety.month_label}` 应为 `{{position_safety.month_label}}`

### Requirement: 占位符维护与数据源校验
系统 SHALL 维护模版中所有 `{{}}` 占位符，并校验每个占位符的数据来源在已定义的数据命名空间（enterprise、employee、contract、training、signature、document、incentive、position_safety 等）中可解析。

#### Scenario: 占位符数据源缺失
- **WHEN** 模版引用了未在任何数据命名空间中定义的占位符
- **THEN** 系统在保存或预检时标记该占位符为无法解析

### Requirement: 真实数据预览
系统 SHALL 提供用真实员工数据替换占位符后的模版预览，使审核老师在生成前确认效果。

#### Scenario: 选择样例员工预览
- **WHEN** 审核老师在模版管理页选择一名已上传的员工进行预览
- **THEN** 系统以该员工真实数据替换 `{{}}` 占位符并渲染出最终效果，包括签名渲染方式
