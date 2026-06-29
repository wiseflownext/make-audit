## ADDED Requirements

### Requirement: 生成文件清单展示
系统 SHALL 在资料包下载界面列出本次生成的全部文件清单，按员工与档案类别组织。

#### Scenario: 展示文件清单
- **WHEN** 一次生成完成
- **THEN** 下载页列出所有生成文件，标明所属员工或公司级类别及文件名

### Requirement: 资料包目录结构
系统 SHALL 按可审核的目录结构组织生成文件，员工档案按员工归集，公司级培训档案单独归集。文件命名 MUST 遵循模版 `meta.yaml` 中的 `output_naming` 规则。

#### Scenario: 按命名规则输出
- **WHEN** 生成某员工的入职须知
- **THEN** 输出文件名遵循该模版的 `output_naming`，如 `员工档案文件资料-{{employee.name}}-2新员工入职需知`

### Requirement: ZIP 打包下载
系统 SHALL 支持将生成的资料包打包为单个 ZIP 文件供一键下载。

#### Scenario: 一键下载压缩包
- **WHEN** 审核老师在下载页点击下载
- **THEN** 系统返回包含完整目录结构与全部文件的 ZIP 压缩包

#### Scenario: 空结果不可打包
- **WHEN** 本次没有任何文件成功生成
- **THEN** 系统不提供下载并提示先完成数据上传与预检
