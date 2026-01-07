# HF Parser - 私募基金周报解析系统

## 📖 项目简介

HF Parser 是一个用于解析和管理私募基金周报数据的全栈系统。系统能够自动解析 Excel 格式的私募基金周报，提取基金、管理人、策略和业绩数据，并提供强大的数据查询、分析和可视化功能。

### 主要功能

- 📊 **数据解析**: 自动解析私募基金周报 Excel 文件，提取结构化数据
- 💾 **数据存储**: 使用 MySQL 存储基金、管理人、策略和业绩数据
- 🔍 **数据查询**: 支持多维度搜索和筛选（按策略、管理人、业绩指标等）
- 📈 **数据分析**: 提供业绩排名、策略分布、多产品对比等分析功能
- 🎨 **数据可视化**: 基于 React 的现代化前端界面，支持图表展示

### 技术栈

**后端:**
- Python 3.11+
- FastAPI - 高性能 Web 框架
- SQLAlchemy 2.0 - ORM 框架
- MySQL 8.0 - 关系型数据库
- Pandas - 数据处理

**前端:**
- React 19 - UI 框架
- TypeScript - 类型安全
- Vite - 构建工具
- Tailwind CSS - 样式框架
- ECharts - 图表库

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- uv (Python 包管理器，推荐使用)

### 1. 克隆项目

```bash
git clone <repository-url> HF_parser
cd HF_parser
```

### 2. 配置 uv 虚拟环境

本项目推荐使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包管理器，它比 pip 更快更可靠。

#### 安装 uv

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 创建虚拟环境并安装依赖

```bash
# 使用 uv 创建虚拟环境并安装依赖（推荐）
uv venv
uv pip install -r requirements.txt

# 激活虚拟环境
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

**或者使用传统方式:**

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置数据库

#### 3.1 创建数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE hf_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hf_user'@'localhost' IDENTIFIED BY 'Abcd1234#';
GRANT ALL PRIVILEGES ON hf_tracker.* TO 'hf_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3.2 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入数据库配置
```

**.env 文件内容:**
```env
# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=hf_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=hf_tracker

# 数据路径
DATA_PDF_PATH=./data/pdf
DATA_EXCEL_PATH=./data/excel

# 日志级别
LOG_LEVEL=INFO
```

### 4. 初始化数据库

```bash
# 确保虚拟环境已激活
# 测试数据库连接
python -c "from src.database.connection import check_connection; print('OK' if check_connection() else 'FAILED')"

# 创建数据表
python -c "from src.database.connection import init_db; init_db()"
```

### 5. 启动后端服务

**方法 1: 使用启动脚本（推荐）**

```bash
# Windows
python start_server.py
# 或直接运行
start_server.bat

# Linux/Mac
python start_server.py
# 或直接运行
chmod +x start_server.sh
./start_server.sh
```

**方法 2: 使用 uvicorn 命令（需要设置 PYTHONPATH）**

```bash
# Windows PowerShell
$env:PYTHONPATH = "$PWD"; python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# Windows CMD
set PYTHONPATH=%CD% && python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# Linux/Mac
PYTHONPATH=. python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将在 `http://localhost:8000` 启动。

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

> **注意**: 如果遇到 `ModuleNotFoundError: No module named 'src'` 错误，请使用启动脚本（方法 1）或设置 PYTHONPATH 环境变量（方法 2）。

### 6. 启动前端服务

打开新的终端窗口：

```bash
cd frontend
npm install
npm run dev
```

前端服务将在 `http://localhost:5173` 启动。

### 7. 导入数据

将周报 Excel 文件放入 `data/excel/` 目录，然后运行导入脚本：

```bash
# 确保在项目根目录，且虚拟环境已激活
python import_1219.py
```

---

## 📁 项目结构

```
HF_parser/
├── README.md                 # 项目主文档（本文件）
├── requirements.txt          # Python 依赖列表
├── .env.example              # 环境变量示例
├── .gitignore                # Git 忽略文件
│
├── src/                      # 后端源代码
│   ├── api/                  # FastAPI 应用
│   │   └── app.py            # 应用入口
│   ├── database/             # 数据库相关
│   │   ├── models.py         # 数据模型
│   │   ├── connection.py     # 数据库连接
│   │   └── queries.py        # 查询函数
│   └── ...
│
├── frontend/                 # 前端源代码
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   │   ├── Dashboard.tsx # 数据总览
│   │   │   ├── Search.tsx    # 产品搜索
│   │   │   └── Compare.tsx    # 产品对比
│   │   ├── components/       # 通用组件
│   │   ├── lib/              # 工具函数
│   │   └── main.tsx          # 入口文件
│   ├── package.json          # 前端依赖
│   └── vite.config.ts        # Vite 配置
│
├── data/                     # 数据文件
│   ├── excel/                # Excel 周报文件
│   └── pdf/                  # PDF 周报文件
│
├── docs/                     # 项目文档
│   ├── API.md                # API 接口文档
│   ├── DATABASE.md           # 数据库设计文档
│   └── DEPLOYMENT.md         # 部署指南
│
├── import_1219.py            # 数据导入脚本示例
├── clean_invalid_strategies.py  # 数据清理脚本
├── start_server.py            # 后端启动脚本（推荐使用）
├── start_server.bat           # Windows 启动脚本
└── start_server.sh            # Linux/Mac 启动脚本
```

### 核心模块说明

- **src/api/**: FastAPI 应用，提供 RESTful API 接口
- **src/database/models.py**: 定义数据库表结构（Manager, Strategy, Fund, FundPerformance 等）
- **src/database/queries.py**: 封装数据库查询逻辑
- **frontend/src/pages/**: 前端页面组件
  - `Dashboard.tsx`: 数据总览页面，支持按日期、策略筛选
  - `Search.tsx`: 产品搜索页面，支持关键词搜索和高级筛选
  - `Compare.tsx`: 产品对比页面，支持多产品指标对比
- **frontend/src/lib/api.ts**: 前端 API 调用封装

---

## 🔧 开发指南

### 后端开发

1. **添加新的 API 端点**

   在 `src/api/` 目录下创建新的路由文件，或在 `app.py` 中添加路由。

2. **修改数据模型**

   编辑 `src/database/models.py`，然后运行数据库迁移。

3. **运行测试**

   ```bash
   # 运行后端测试（如果有）
   pytest
   ```

### 前端开发

1. **添加新页面**

   在 `frontend/src/pages/` 目录下创建新的页面组件，并在 `App.tsx` 中添加路由。

2. **修改 API 调用**

   编辑 `frontend/src/lib/api.ts` 文件。

3. **运行测试**

   ```bash
   cd frontend
   npm test
   ```

---

## 📚 文档

- [API 接口文档](docs/API.md) - 详细的 API 接口说明
- [数据库设计文档](docs/DATABASE.md) - 数据库表结构和关系
- [部署指南](docs/DEPLOYMENT.md) - 生产环境部署说明

---

## 🛠️ 常用命令

### 后端

```bash
# 启动开发服务器（推荐使用启动脚本）
python start_server.py
# 或
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# 运行数据导入
python import_1219.py

# 清理无效策略
python clean_invalid_strategies.py
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

---

## ⚙️ 配置说明

### 环境变量

所有配置项都在 `.env` 文件中，参考 `.env.example` 进行配置。

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| MYSQL_HOST | MySQL 主机地址 | localhost |
| MYSQL_PORT | MySQL 端口 | 3306 |
| MYSQL_USER | MySQL 用户名 | - |
| MYSQL_PASSWORD | MySQL 密码 | - |
| MYSQL_DATABASE | 数据库名 | hf_tracker |
| LOG_LEVEL | 日志级别 | INFO |

### 前端 API 地址配置

如需修改后端 API 地址，编辑 `frontend/src/lib/api.ts`:

```typescript
const API_BASE_URL = 'http://localhost:8000/api'  // 修改为实际地址
```

---

## 🐛 常见问题

### 1. ModuleNotFoundError: No module named 'src'

**错误**: 运行 uvicorn 时提示找不到 `src` 模块

**解决方案**:
- **推荐**: 使用启动脚本 `python start_server.py`
- **或者**: 设置 PYTHONPATH 环境变量：
  ```bash
  # Windows PowerShell
  $env:PYTHONPATH = "$PWD"
  
  # Windows CMD
  set PYTHONPATH=%CD%
  
  # Linux/Mac
  export PYTHONPATH=$(pwd)
  ```
- **或者**: 在项目根目录运行命令时添加 PYTHONPATH：
  ```bash
  PYTHONPATH=. python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
  ```

### 2. 数据库连接失败

**错误**: `sqlalchemy.exc.OperationalError: Can't connect to MySQL server`

**解决方案**:
- 检查 MySQL 服务是否启动
- 检查 `.env` 中的数据库配置是否正确
- 检查防火墙是否允许 3306 端口

### 3. 前端无法连接后端

**错误**: `Network Error` 或 `CORS Error`

**解决方案**:
- 确保后端服务已启动（http://localhost:8000）
- 检查 `src/api/app.py` 中的 CORS 配置
- 检查前端 API 地址配置

### 4. 导入数据时报错

**错误**: `KeyError` 或 `ValueError`

**解决方案**:
- 检查 Excel 文件格式是否正确
- 检查列名是否匹配
- 查看日志文件获取详细错误信息

更多问题请参考 [部署指南](docs/DEPLOYMENT.md#6-常见问题)。

---

## 📝 许可证

本项目仅供内部使用。

---

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📞 联系方式

如有问题，请通过以下方式联系：
- 提交 GitHub Issue
- 联系项目维护者

---

*最后更新: 2025-01-07*

