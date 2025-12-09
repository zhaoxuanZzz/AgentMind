#!/bin/bash

# ============================================
# Agent System 数据库备份脚本
# ============================================
# 说明：本脚本用于备份PostgreSQL数据库
# 支持Docker和本地PostgreSQL两种方式
# ============================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 默认配置
DB_NAME="${DB_NAME:-agentsys}"
DB_USER="${DB_USER:-agentsys}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
USE_DOCKER="${USE_DOCKER:-false}"
DOCKER_CONTAINER="${DOCKER_CONTAINER:-agentsys-postgres}"

# 生成备份文件名
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql"
BACKUP_FILE_GZ="$BACKUP_FILE.gz"

echo "========================================"
echo "  Agent System 数据库备份"
echo "========================================"
echo ""
echo "数据库配置:"
echo "  数据库名: $DB_NAME"
echo "  用户名: $DB_USER"
echo "  主机: $DB_HOST"
echo "  端口: $DB_PORT"
echo "  备份目录: $BACKUP_DIR"
echo "  使用Docker: $USE_DOCKER"
if [ "$USE_DOCKER" = "true" ]; then
    echo "  Docker容器: $DOCKER_CONTAINER"
fi
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行备份
echo -e "${YELLOW}正在备份数据库...${NC}"

if [ "$USE_DOCKER" = "true" ]; then
    # Docker方式备份
    if ! docker ps | grep -q "$DOCKER_CONTAINER"; then
        echo -e "${RED}错误: Docker容器 $DOCKER_CONTAINER 未运行${NC}"
        exit 1
    fi
    
    docker exec "$DOCKER_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE_GZ"
else
    # 本地PostgreSQL备份
    # 检查pg_dump是否可用
    if ! command -v pg_dump &> /dev/null; then
        echo -e "${RED}错误: 未找到 pg_dump 命令，请安装PostgreSQL客户端${NC}"
        exit 1
    fi
    
    # 执行备份（需要设置PGPASSWORD环境变量或使用.pgpass文件）
    export PGPASSWORD="${PGPASSWORD:-}"
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_FILE" 2>/dev/null || \
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE_GZ"
fi

# 检查备份是否成功
if [ -f "$BACKUP_FILE_GZ" ] || [ -f "$BACKUP_FILE" ]; then
    if [ -f "$BACKUP_FILE_GZ" ]; then
        BACKUP_SIZE=$(ls -lh "$BACKUP_FILE_GZ" | awk '{print $5}')
        echo -e "${GREEN}✓${NC} 数据库备份完成"
        echo "  备份文件: $BACKUP_FILE_GZ"
        echo "  文件大小: $BACKUP_SIZE"
    else
        BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
        echo -e "${GREEN}✓${NC} 数据库备份完成"
        echo "  备份文件: $BACKUP_FILE"
        echo "  文件大小: $BACKUP_SIZE"
    fi
else
    echo -e "${RED}✗${NC} 备份失败：备份文件未生成"
    exit 1
fi

echo ""
echo "========================================"
echo "  备份完成"
echo "========================================"
echo ""
echo "使用方法:"
echo "  1. Docker方式: USE_DOCKER=true ./backup_database.sh"
echo "  2. 本地方式: DB_HOST=localhost DB_USER=agentsys DB_NAME=agentsys ./backup_database.sh"
echo "  3. 自定义目录: BACKUP_DIR=/path/to/backups ./backup_database.sh"
echo ""

