## ADDED Requirements

### Requirement: 签名为可选上传
系统 SHALL 将员工手写签名照片设为非必填项。上传与否都不得阻塞资料包生成。

#### Scenario: 未上传任何签名
- **WHEN** 审核老师不上传任何签名照片即触发生成
- **THEN** 系统正常生成全部资料，所有签名位置使用非打印体文本签名（如员工姓名的手写风格字体）

#### Scenario: 上传部分员工签名
- **WHEN** 仅部分员工上传了签名照片
- **THEN** 已上传者使用电子签名图片，未上传者使用非打印体文本签名

### Requirement: 签名照片抠底处理
系统 SHALL 对上传的手写签名照片进行去底处理，生成背景透明的电子签名图片，避免打印体造成的失真。

#### Scenario: 抠底生成电子签名
- **WHEN** 审核老师上传一张白底手写签名照片
- **THEN** 系统输出背景透明的电子签名图片，并关联到对应员工的 `employee.signature`

#### Scenario: 签名照片与员工匹配
- **WHEN** 上传的签名文件按约定命名或映射到某员工
- **THEN** 系统将处理后的电子签名绑定到该员工，渲染时在签名位置使用该图片

### Requirement: 管理人员签名回退
系统 SHALL 对管理人员类签名（如 `signature.hr_manager`、`signature.department_head`、`signature.prepared_by` 等）应用与员工签名一致的可选规则。

#### Scenario: 管理人员未上传签名
- **WHEN** 某管理人员签名位未提供签名图片
- **THEN** 系统在该位置使用非打印体文本签名而非留空打印体
