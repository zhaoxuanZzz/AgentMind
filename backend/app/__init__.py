# App module

import sys
import os

# 确保 backend 目录在 Python 路径中
# 这样可以使用 "from app.xxx import yyy" 的方式导入
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
