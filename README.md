# HR 审核资料生成器

为汽车零配件生产企业的审核老师提供一键式人力资源审核资料包生成服务：上传员工花名册与可选签名后，按内置模版与体系规则自动生成整套档案并打包下载。

---

## 目录结构

```
make-audit/
├── backend/                # FastAPI 后端服务
│   ├── app/
│   │   ├── main.py         # FastAPI 应用入口
│   │   ├── api/            # 路由层
│   │   ├── core/           # 配置与公共工具
│   │   ├── models/         # 数据模型（员工、企业、培训等）
│   │   ├── services/       # 业务逻辑（渲染、生成、打包）
│   │   └── templates/      # 模版加载与占位符解析
│   ├── tests/              # pytest 测试
│   └── requirements.txt
├── frontend/               # React Web 前端
│   ├── src/
│   │   ├── pages/          # 上传页 / 下载页 / 模版管理页
│   │   ├── components/     # 共用 UI 组件
│   │   └── api/            # 后端接口封装
│   └── package.json
├── template/人力资源/       # 内置模版资产（meta.yaml + template.html）
└── json文件/               # 培训计划等结构化数据
```

---

## 本地启动

### 后端

**依赖**：Python ≥ 3.11

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

访问 API 文档：http://localhost:8000/docs

### 前端

**依赖**：Node.js ≥ 18

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5174

### 一键启动（推荐）

```bash
./scripts/dev.sh
```

同时启动后端（8000）与前端（5174）。首次运行会自动创建虚拟环境并安装依赖。

---

## 运行测试

```bash
# 后端
cd backend && python -m pytest -v

# 前端
cd frontend && npm test
```

---

## 关键约定

| 项目 | 约定 |
|------|------|
| 占位符格式 | `{{namespace.key}}`，例如 `{{employee.name}}` |
| 命名空间 | `enterprise` / `employee` / `contract` / `training` / `signature` / `document` / `incentive` / `position_safety` |
| 当前年 | 取服务器系统年份（`datetime.date.today().year`） |
| 节假日来源 | 内置近三年公开节假日表（来源：万年历） |
| 模版编辑 | 覆盖内置模版（不按客户分版本） |
| 工作日历 | 单休（默认周日休息），可在 `core/calendar.py` 配置节假日 |
| 个人培训记录 | 仅含年度培训计划参与记录，不含入司 6 门培训 |
| 入司 6 门培训 | 记录在岗位培训评价表（转正档案），不进个人培训记录表 |
| 签名可选 | 未上传时自动回退非打印体文本签名，不阻塞生成 |
| PDF 输出 | WeasyPrint + 内置打印 CSS，中文字体固定 SimSun |

---

## 功能概览

1. **上传资料**：企业基础信息 + 员工花名册（Excel/CSV）+ 可选签名照片
2. **自动生成**：入职/转正/满意度档案、年度培训计划、培训签到记录、个人培训记录表
3. **模版管理**：在线浏览/编辑/保存模版，占位符校验，真实数据预览
4. **下载资料包**：按审核目录结构组织，一键打包 ZIP 下载
