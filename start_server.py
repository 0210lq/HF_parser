"""
启动后端服务器的辅助脚本
自动设置 PYTHONPATH 并启动 uvicorn
"""
import os
import sys
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.absolute()

# 将项目根目录添加到 Python 路径
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置 PYTHONPATH 环境变量（用于子进程）
os.environ['PYTHONPATH'] = str(project_root)

if __name__ == "__main__":
    import uvicorn
    
    # 启动服务器
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root)]
    )

