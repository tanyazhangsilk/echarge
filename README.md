# E-Charge 聚合平台（毕业设计骨架）

本项目基于原型设计 [`E-Charge 管理平台`](https://v0-e-charge-platform-design-2a.vercel.app/) 搭建，采用 **前后端分离架构**：

- 前端：Vue 3 + Vite + Element Plus
- 后端：Python + FastAPI
- 数据库：MySQL（通过 SQLAlchemy 连接）

---

## 项目目录结构总览

```text
.
├── backend/                 # 后端代码根目录
│   └── app/
│       ├── api/
│       │   └── v1/
│       │       ├── __init__.py
│       │       └── routes.py          # v1 API 路由与假数据（对应概览页）
│       ├── core/
│       │   └── config.py              # 环境配置与 MySQL 连接字符串生成
│       ├── db/
│       │   └── session.py             # SQLAlchemy Engine / Session 工厂与 get_db 依赖
│       ├── models/                    # SQLAlchemy 模型（待逐步扩展）
│       ├── schemas/                   # Pydantic Schema（待逐步扩展）
│       └── app.py                     # FastAPI app 实例与路由挂载
│
├── frontend/               # 前端 Vue 3 + Vite 项目
│   ├── src/
│   │   ├── api/
│   │   │   ├── http.js               # Axios 实例，默认使用 /api/v1（由 Vite 代理到后端）
│   │   │   └── overview.js           # 概览相关 API 封装
│   │   ├── layouts/
│   │   │   └── MainLayout.vue        # 主框架：侧边栏 + 顶栏 + router-view
│   │   ├── router/
│   │   │   └── index.js              # Vue Router 路由配置
│   │   ├── views/
│   │   │   ├── Dashboard.vue         # 概览页（仪表盘）
│   │   │   └── PlaceholderPage.vue   # 其他功能占位页
│   │   ├── App.vue                   # 根组件，使用 MainLayout
│   │   └── main.js                   # Vue 入口，挂载 Element Plus / Router / Pinia
│   └── ...                           # Vite 默认文件（package.json、vite.config.js 等）
│
├── main.py                # Uvicorn 入口：导出 backend.app.app.app
├── requirements.txt       # Python 依赖
└── README.md
```

---

## 后端启动方式（FastAPI）

### 1. 创建并启动虚拟环境（建议）

```bash
cd e:/myproject
python -m venv venv
venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

### 2. 设置数据库连接（MySQL）

在项目根目录创建 `.env` 文件（可按实际环境修改）：

```env
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=e_charge

# 或者直接给完整连接字符串（会覆盖上面配置）
# SQLALCHEMY_DATABASE_URI=mysql+pymysql://user:password@host:3306/dbname
```

`backend/app/core/config.py` 会根据这些变量生成 `mysql+pymysql://...` 连接字符串，供 SQLAlchemy 使用。

### 3. 启动后端服务

```bash
uvicorn main:app --reload --port 8000
```

启动完成后，主要测试端点：

- 健康检查：`GET http://localhost:8000/api/v1/health`
- 概览卡片数据：`GET http://localhost:8000/api/v1/overview/summary`
- 实时充电订单：`GET http://localhost:8000/api/v1/overview/realtime-orders`

---

## 前端启动方式（Vue 3 + Element Plus）

```bash
cd e:/myproject/frontend
npm install        # 已在本次初始化执行过，首次建议再确认一次
npm run dev
```

默认会在 `http://localhost:5173` 启动开发服务器。

前端通过 `src/api/http.js` 访问后端：

- `VITE_API_BASE_URL`（若在 `frontend/.env` 设置），例如：

  ```env
  VITE_API_BASE_URL=http://localhost:8000/api/v1
  ```

- 若未设置，默认使用相对路径 `/api/v1`，并由 `vite.config.js` 代理到 `http://localhost:8000/api/v1`（可避免浏览器 CORS）。

---

## 对应原型的基础框架说明

根據原型 [`E-Charge 管理平台`](https://v0-e-charge-platform-design-2a.vercel.app/)：

- **左侧导航菜单**：在 `MainLayout.vue` 中使用 Element Plus `el-menu` 实现，包括：
  - 概览
  - 订单管理（历史订单 / 实时订单 / 异常订单）
  - 财务管理（绑卡管理 / 收益对账 / 开票管理）
  - 电站电桩管理（电站列表 / 电桩管理 / 电价设置 / 审核管理）
  - 机构管理（运营商资料 / 专属机构）
  - 用户管理（专属用户 / 车队管理 / 白名单管理）
  - 营销管理（标签管理 / 折扣管理）
  - 系统设置

- **顶部栏位**：展示当前页面标题与用户信息：
  - 角色：运营商管理员
  - 账号：`admin@echarge.com`

- **概览页（Dashboard）**：
  - 四张统计卡片：今日订单、今日收益、在线电桩、活跃用户
  - 两块图表区域（目前保留为“预留图表区”，后续可接入 ECharts / AntV 等）
  - “实时充电订单”表格，数据来自后端假数据 API

后续你可以在 `views/` 目录下为每个二级菜单建立独立页面，并对应到后端 `backend/app/api/v1/` 中的具体业务路由与数据模型。

---

## 下一步建议

- 在 `backend/app/models/` 定义核心实体（电站、电桩、订单、用户、运营商等）并建立 Alembic 迁移。
- 在 `backend/app/api/v1/` 按业务模块拆分路由文件（如 `orders.py`、`stations.py` 等）。
- 在前端 `views/` 下，逐步将 `PlaceholderPage.vue` 替换为真实的功能页面。

