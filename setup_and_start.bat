@echo off
chcp 65001 >nul
echo ========================================
echo HF Parser - 一键初始化和启动
echo ========================================
echo.

REM 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在！
    echo 请先运行: python -m venv .venv
    pause
    exit /b 1
)

REM 激活虚拟环境
echo [1/5] 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 安装依赖 (如果需要)
echo.
echo [2/5] 检查Python依赖...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo 需要安装依赖...
    pip install -r requirements.txt
) else (
    echo 依赖已安装 ✓
)

REM 测试数据库连接
echo.
echo [3/5] 测试数据库连接...
python -c "from src.database.connection import check_connection; import sys; sys.exit(0 if check_connection() else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo [警告] 数据库连接失败！
    echo.
    echo 请先运行以下命令创建数据库:
    echo   mysql -u root -p ^< init_database.sql
    echo.
    echo 或手动执行 init_database.sql 中的SQL语句
    echo.
    pause
    exit /b 1
) else (
    echo 数据库连接成功 ✓
)

REM 初始化数据库表
echo.
echo [4/5] 初始化数据库表...
python -c "from src.database.connection import init_db; init_db()"
if errorlevel 1 (
    echo 数据库表初始化失败！
    pause
    exit /b 1
) else (
    echo 数据库表初始化成功 ✓
)

REM 启动后端服务
echo.
echo [5/5] 启动后端服务...
echo.
echo ========================================
echo 后端服务启动中...
echo API 文档: http://localhost:8000/docs
echo 健康检查: http://localhost:8000/health
echo ========================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python start_server.py
