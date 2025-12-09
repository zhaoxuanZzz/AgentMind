#!/bin/bash
# ========================================
# 启动后端开发服务器
# ========================================

echo ""
echo "======================================"
echo "  启动后端开发服务器"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 激活虚拟环境（支持 venv 和 conda）
echo -e "${YELLOW}[1/3] 激活虚拟环境...${NC}"

# 检查是否有 conda
if command -v conda &> /dev/null; then
    # conda 可用，尝试激活 agentsys 环境
    echo "检测到 conda，尝试激活环境..."
    
    # 初始化 conda（如果需要）
    eval "$(conda shell.bash hook)" 2>/dev/null || true
    
    # 尝试激活 agentsys 环境
    conda activate agentsys 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "未找到 agentsys conda 环境，尝试激活 base 环境..."
        conda activate base
    fi
elif [ -f "venv/bin/activate" ]; then
    # 使用 venv
    echo "使用 venv 虚拟环境..."
    source venv/bin/activate
else
    echo -e "${RED}[警告] 未找到虚拟环境${NC}"
    echo ""
    echo "请选择一种方式创建虚拟环境:"
    echo "  1. 使用 conda: conda create -n agentsys python=3.11"
    echo "  2. 使用 venv: python -m venv venv"
    echo ""
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${RED}[警告] .env 文件不存在${NC}"
    echo "请复制 ../env.template 为 .env 并配置 API Key"
    exit 1
fi

echo ""
echo -e "${YELLOW}[2/3] 检查依赖...${NC}"
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[警告] 依赖未安装，正在安装...${NC}"
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo ""
echo -e "${YELLOW}[3/3] 启动服务器...${NC}"
echo ""
echo "======================================"
echo "  服务器信息"
echo "======================================"
echo -e "  - API地址: ${GREEN}http://localhost:8000${NC}"
echo -e "  - API文档: ${GREEN}http://localhost:8000/docs${NC}"
echo "  - 工作目录: $(pwd)"
echo "======================================"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo ""

# 设置 PYTHONPATH 并启动
export PYTHONPATH=$(pwd)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

