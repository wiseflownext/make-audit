## 1. 模版与命名空间

- [x] 1.1 培训评价表 HTML 改为 `LIST:onboarding_training_rows` 循环区
- [x] 1.2 注册 `onboarding.*` 命名空间并更新 meta.yaml / template.json

## 2. 生成规则

- [x] 2.1 实现 `build_onboarding_training_list_data()` 与综管部培训人解析
- [x] 2.2 在 `generate_probation_docs()` 中注入 list_data 并自动解析 hr_manager
- [x] 2.3 生成 API 传入完整花名册供解析

## 3. 预览与测试

- [x] 3.1 模版预览 API 注入示例培训明细行
- [x] 3.2 新增单元测试覆盖工作日推算与综管部负责人解析
