# 快速部署指南

本文档提供在新服务器或本地机器上快速部署 HF Parser 系统的详细步骤。

## 目录

1. [环境准备](#1-环境准备)
2. [后端部署](#2-后端部署)
3. [前端部署](#3-前端部署)
4. [数据导入](#4-数据导入)
5. [生产环境部署](#5-生产环境部署)
6. [常见问题](#6-常见问题)

---

## 1. 环境准备

### 1.1 系统要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| 操作系统 | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| Python | 3.11 | 3.11+ |
| Node.js | 18.0 | 20.0+ |
| MySQL | 8.0 | 8.0+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 10GB | 20GB+ |

### 1.2 安装 Python

**Windows:**
```powershell
# 下载并安装 Python 3.11+
# https://www.python.org/downloads/

# 验证安装
python --version
pip --version
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 --version
```

### 1.3 安装 Node.js

**Windows:**
```powershell
# 下载并安装 Node.js 18+
# https://nodejs.org/

# 验证安装
node --version
npm --version
```

**Linux (Ubuntu):**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

### 1.4 安装 MySQL

**Windows:**
```powershell
# 下载并安装 MySQL 8.0
# https://dev.mysql.com/downloads/mysql/

# 或使用 Chocolatey
choco install mysql
```

**Linux (Ubuntu):**
```bash
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置
sudo mysql_secure_installation
```

### 1.5 创建数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE hf_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hf_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON hf_tracker.* TO 'hf_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 2. 后端部署

### 2.1 获取代码

```bash
# 克隆项目（或解压项目压缩包）
git clone <repository-url> HF_parser
cd HF_parser
```

### 2.2 创建虚拟环境

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 2.3 安装依赖

```bash
pip install -r requirements.txt
```

### 2.4 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
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

### 2.5 初始化数据库

```bash
# 测试数据库连接
python -c "from src.database.connection import check_connection; print('OK' if check_connection() else 'FAILED')"

# 创建数据表
python -c "from src.database.connection import init_db; init_db()"
```

### 2.6 启动后端服务

**开发模式:**
```bash
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

**验证服务:**
```bash
# 访问 API 文档
curl http://localhost:8000/docs

# 测试健康检查
curl http://localhost:8000/health
```

---

## 3. 前端部署

### 3.1 安装依赖

```bash
cd frontend
npm install
```

### 3.2 配置 API 地址

如需修改后端 API 地址，编辑 `frontend/src/lib/api.ts`:

```typescript
const API_BASE_URL = 'http://localhost:8000/api'  // 修改为实际地址
```

### 3.3 启动前端服务

**开发模式:**
```bash
npm run dev
```

**验证服务:**
```bash
# 访问前端页面
# http://localhost:5173
```

---

## 4. 数据导入

### 4.1 准备数据文件

将周报 Excel 文件放入 `data/excel/` 目录：

```
data/
└── excel/
    ├── 私募周报1205.xlsx  # 用于获取产品代码映射
    └── 私募周报1219.xlsx  # 要导入的周报数据
```

### 4.2 运行导入脚本

```bash
# 确保在项目根目录，且虚拟环境已激活
python import_1219.py
```

**预期输出:**
```
=====================================
Starting 1219 Weekly Report Import
=====================================
Built name->code mapping: 5491 entries
Parsed 1219 Excel: 4076 total records
  Matched: 3974, Generated codes: 102
Inserting strategies...
Strategies: 23 new
Inserting managers...
Managers: 1434 new
Inserting funds and performance...
Import completed:
  Strategies: 23
  Managers: 1434
  Funds: 4076 new, 0 updated
  Performances: 4076
=====================================
```

### 4.3 验证数据

```bash
# 通过 API 验证
curl http://localhost:8000/api/analytics/stats
```

**预期响应:**
```json
{
  "total_managers": 1434,
  "total_strategies": 23,
  "total_funds": 4076,
  "total_performances": 4076,
  "latest_report_date": "2025-12-19"
}
```

---

## 5. 生产环境部署

### 5.1 后端生产部署

#### 使用 Gunicorn (Linux)

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn src.api.app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### 使用 Systemd 服务

创建 `/etc/systemd/system/hf-parser.service`:

```ini
[Unit]
Description=HF Parser API Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/HF_parser
Environment="PATH=/path/to/HF_parser/venv/bin"
ExecStart=/path/to/HF_parser/venv/bin/gunicorn src.api.app:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable hf-parser
sudo systemctl start hf-parser
sudo systemctl status hf-parser
```

### 5.2 前端生产构建

```bash
cd frontend

# 构建生产版本
npm run build

# 构建产物在 dist/ 目录
```

### 5.3 Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/HF_parser/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx
```

### 5.4 Docker 部署 (可选)

**Dockerfile (后端):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MYSQL_HOST=db
      - MYSQL_PORT=3306
      - MYSQL_USER=hf_user
      - MYSQL_PASSWORD=your_password
      - MYSQL_DATABASE=hf_tracker
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=hf_tracker
      - MYSQL_USER=hf_user
      - MYSQL_PASSWORD=your_password
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - api

volumes:
  mysql_data:
```

---

## 6. 常见问题

### Q1: 数据库连接失败

**错误信息:**
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")
```

**解决方案:**
1. 检查 MySQL 服务是否启动
2. 检查 `.env` 中的数据库配置
3. 检查防火墙是否允许 3306 端口

```bash
# 检查 MySQL 状态
sudo systemctl status mysql

# 测试连接
mysql -h localhost -u hf_user -p hf_tracker
```

### Q2: 前端无法连接后端

**错误信息:**
```
Network Error / CORS Error
```

**解决方案:**
1. 确保后端服务已启动
2. 检查 `src/api/app.py` 中的 CORS 配置
3. 检查前端 API 地址配置

```python
# 添加前端地址到 CORS 允许列表
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://your-domain.com"],
    ...
)
```

### Q3: 导入数据时报错

**错误信息:**
```
KeyError: 'xxx' / ValueError: could not convert string to float
```

**解决方案:**
1. 检查 Excel 文件格式是否正确
2. 检查列名是否与 `COLUMN_MAP` 匹配
3. 检查数据中是否有异常值

### Q4: 内存不足

**解决方案:**
1. 增加服务器内存
2. 减少 Gunicorn worker 数量
3. 分批导入数据

### Q5: 端口被占用

**错误信息:**
```
Address already in use
```

**解决方案:**
```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :8000

# Linux
lsof -i :8000

# 终止进程或更换端口
```

---

## 快速检查清单

部署完成后，请确认以下项目：

- [ ] MySQL 服务运行正常
- [ ] 数据库和用户创建成功
- [ ] `.env` 配置正确
- [ ] 后端服务启动成功 (http://localhost:8000/health)
- [ ] API 文档可访问 (http://localhost:8000/docs)
- [ ] 前端服务启动成功 (http://localhost:5173)
- [ ] 数据导入成功
- [ ] 前端页面数据显示正常

---

## 联系支持

如遇到无法解决的问题，请提供以下信息：

1. 操作系统版本
2. Python/Node.js 版本
3. 完整的错误日志
4. `.env` 配置（隐藏密码）
5. 执行的命令和步骤
