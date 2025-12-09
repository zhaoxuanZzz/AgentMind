#!/bin/bash
# ========================================
# 清理 Python 缓存文件
# ========================================

echo ""
echo "======================================"
echo "  清理 Python __pycache__ 目录"
echo "======================================"
echo ""

# 切换到脚本所在目录的父目录
cd "$(dirname "$0")/.."

echo "正在查找 __pycache__ 目录..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "正在查找 .pyc 文件..."
find . -type f -name "*.pyc" -delete 2>/dev/null

echo ""
echo "======================================"
echo "  清理完成！"
echo "======================================"
echo ""

