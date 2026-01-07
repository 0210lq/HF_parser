# 快速启动指南

## 项目已创建的文件

已成功创建以下后端代码文件:
- `src/__init__.py` - 包初始化
- `src/database/__init__.py` - 数据库包初始化
- `src/database/models.py` - 数据模型定义 (5个模型: Manager, Strategy, Fund, FundPerformance, ReportMetadata)
- `src/database/connection.py` - 数据库连接管理
- `src/database/queries.py` - 数据库查询函数
- `src/api/__init__.py` - API包初始化
- `src/api/app.py` - FastAPI应用 (包含所有API接口)
- `init_database.sql` - MySQL数据库初始化脚本

## 启动步骤

### 1. 初始化MySQL数据库

**选项A: 使用MySQL命令行 (推荐)**
```bash
# 使用root用户登录MySQL并运行初始化脚本
# 请将 <your-root-password> 替换为你的MySQL root密码
mysql -u root -p < init_database.sql
```

**选项B: 使用MySQL Workbench或其他GUI工具**
1. 打开MySQL Workbench
2. 连接到本地MySQL服务器(root用户)
3. 打开 `init_database.sql` 文件
4. 执行整个脚本

**选项C: 手动执行SQL命令**
```sql
CREATE DATABASE IF NOT EXISTS hf_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'hf_user'@'localhost' IDENTIFIED BY 'Abcd1234#';
GRANT ALL PRIVILEGES ON hf_tracker.* TO 'hf_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 创建数据库表

激活虚拟环境并创建表:
```bash
# Windows
.venv\Scripts\activate

# 初始化数据库表
python -c "from src.database.connection import init_db; init_db()"
```

### 3. 启动后端服务

**选项A: 使用启动脚本 (推荐)**
```bash
# Windows
python start_server.py
# 或
start_server.bat
```

**选项B: 使用uvicorn命令**
```bash
# 确保虚拟环境已激活
.venv\Scripts\activate

# 启动服务
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将在以下地址启动:
- **API基础地址**: http://localhost:8000/api
- **API文档 (Swagger)**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 4. 启动前端服务

打开新的终端窗口:
```bash
cd frontend
npm install
npm run dev
```

前端服务将在 http://localhost:5173 启动

### 5. 导入数据 (可选)

如果你有周报Excel文件，将其放入 `data/excel/` 目录，然后运行:
```bash
python import_1219.py
```

## 验证安装

### 测试数据库连接
```bash
.venv\Scripts\activate
python -c "from src.database.connection import check_connection; print('OK' if check_connection() else 'FAILED')"
```

### 测试API
访问 http://localhost:8000/docs 查看API文档

### 测试前端
访问 http://localhost:5173 查看前端界面

## 常见问题

### 1. 数据库连接失败
```
Error: Access denied for user 'hf_user'@'localhost'
```
**解决方案**: 运行 `init_database.sql` 创建数据库和用户

### 2. ModuleNotFoundError: No module named 'src'
**解决方案**: 使用 `start_server.py` 或 `start_server.bat` 启动服务

### 3. 前端无法连接后端
**解决方案**:
- 确保后端服务已启动 (http://localhost:8000)
- 检查CORS配置 (已在 `src/api/app.py` 中配置)

## 项目结构

```
HF_parser/
├── src/                      # ✅ 后端代码 (已创建)
│   ├── api/
│   │   └── app.py           # FastAPI应用
│   └── database/
│       ├── models.py        # 数据模型
│       ├── connection.py    # 数据库连接
│       └── queries.py       # 查询函数
├── frontend/                 # 前端代码 (已存在)
├── data/                     # 数据文件目录
├── init_database.sql         # ✅ 数据库初始化脚本 (已创建)
├── start_server.py           # 启动脚本
├── .env                      # 环境变量配置
└── README.md                 # 项目文档
```

## 下一步

1. ✅ 运行 `init_database.sql` 创建数据库
2. ✅ 运行 `python start_server.py` 启动后端
3. ✅ 运行 `cd frontend && npm run dev` 启动前端
4. 📊 导入数据 (如果有周报文件)
5. 🎉 开始使用系统!
