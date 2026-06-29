## ADDED Requirements

### Requirement: 企业基础资料录入
系统 SHALL 提供分模块的客户基础资料录入界面，人力模块 MUST 至少采集企业名称等用于资料页眉与落款的企业字段。

#### Scenario: 录入企业名称
- **WHEN** 审核老师在人力模块填写企业名称并保存
- **THEN** 系统持久化该企业资料，并在后续生成的所有模版中以 `{{enterprise.name}}` 渲染该值

#### Scenario: 缺少必填企业字段
- **WHEN** 审核老师未填写企业名称即尝试进入生成
- **THEN** 系统阻止生成并提示缺失的企业必填字段

### Requirement: 员工花名册上传
系统 SHALL 支持上传员工花名册文件（Excel/CSV），并解析为结构化员工主数据。花名册 MUST 覆盖姓名、部门、岗位、入职日期、是否重点岗位、是否内审员、是否普通员工等字段。

#### Scenario: 成功上传并解析花名册
- **WHEN** 审核老师上传符合列结构的花名册文件
- **THEN** 系统解析每一行为一名员工记录，并展示解析后的员工列表供确认

#### Scenario: 花名册缺少必需列
- **WHEN** 上传的花名册缺少姓名、部门、岗位或入职日期等必需列
- **THEN** 系统拒绝该文件并明确提示缺失的列名

### Requirement: 员工字段标准化与校验
系统 SHALL 对解析出的员工数据进行标准化与校验，确保所有模版 `{{employee.*}}` 占位符均能从员工主数据解析到取值。员工主数据 MUST 支持以下字段：name、department_name、position_name、position_category、gender、id_no、birth_date、hire_date、phone、education、school、address、remark、is_key_position、is_internal_auditor、is_regular_employee、is_manager、employment_status。

#### Scenario: 身份证派生字段
- **WHEN** 员工记录提供了身份证号但未提供出生年月或性别
- **THEN** 系统从身份证号推导出生年月与性别并回填员工记录

#### Scenario: 占位符无法解析时预检报错
- **WHEN** 某模版引用了 `{{employee.x}}` 而该字段在员工主数据中不存在或为空
- **THEN** 系统在预检阶段报告该模版与缺失字段，提示补录后再生成

#### Scenario: 重点岗位与内审员标识
- **WHEN** 花名册中某员工被标记为重点岗位或内审员
- **THEN** 系统在员工主数据上保留该布尔标识，供培训面向对象匹配使用
