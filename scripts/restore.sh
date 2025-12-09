#!/bin/bash

# Agent System 数据恢复脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ $# -lt 1 ]; then
    echo "用法: $0 <备份目录或备份文件前缀>"
    echo ""
    echo "示例:"
    echo "  $0 backups/20241024_120000"
    echo "  $0 backups  # 恢复最新备份"
    exit 1
fi

BACKUP_PATH=$1

echo "========================================"
echo "  Agent System 数据恢复"
echo "========================================"
echo ""

# 如果指定的是目录，查找最新备份
if [ -d "$BACKUP_PATH" ]; then
    echo "正在查找最新备份..."
    LATEST=$(ls -t "$BACKUP_PATH"/postgres_*.sql.gz 2>/dev/null | head -1)
    if [ -z "$LATEST" ]; then
        echo -e "${RED}错误: 未找到备份文件${NC}"
        exit 1
    fi
    BACKUP_PREFIX=$(basename "$LATEST" | sed 's/postgres_\(.*\)\.sql\.gz/\1/')
    BACKUP_DIR=$(dirname "$LATEST")
else
    BACKUP_DIR=$(dirname "$BACKUP_PATH")
    BACKUP_PREFIX=$(basename "$BACKUP_PATH")
fi

POSTGRES_FILE="$BACKUP_DIR/postgres_${BACKUP_PREFIX}.sql.gz"
CHROMA_FILE="$BACKUP_DIR/chroma_${BACKUP_PREFIX}.tar.gz"
REDIS_FILE="$BACKUP_DIR/redis_${BACKUP_PREFIX}.rdb"

echo "备份标识: $BACKUP_PREFIX"
echo "备份目录: $BACKUP_DIR"
echo ""

# 确认操作
echo -e "${YELLOW}警告: 此操作将覆盖当前数据！${NC}"
read -p "确定要继续吗？(yes/no) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "已取消恢复操作"
    exit 0
fi

# 恢复PostgreSQL
if [ -f "$POSTGRES_FILE" ]; then
    echo -e "${YELLOW}正在恢复 PostgreSQL...${NC}"
    
    # 先清空现有数据库
    docker exec agentsys-postgres psql -U agentsys -d postgres -c "DROP DATABASE IF EXISTS agentsys;"
    docker exec agentsys-postgres psql -U agentsys -d postgres -c "CREATE DATABASE agentsys;"
    
    # 恢复数据
    gunzip -c "$POSTGRES_FILE" | docker exec -i agentsys-postgres psql -U agentsys agentsys
    echo -e "${GREEN}✓${NC} PostgreSQL 恢复完成"
else
    echo -e "${RED}✗${NC} PostgreSQL 备份文件不存在: $POSTGRES_FILE"
fi

# 恢复ChromaDB
if [ -f "$CHROMA_FILE" ]; then
    echo -e "${YELLOW}正在恢复 ChromaDB...${NC}"
    
    # 停止ChromaDB容器
    docker-compose stop chromadb
    
    # 清空现有数据
    docker run --rm -v agentsys_chroma_data:/data alpine rm -rf /data/*
    
    # 恢复数据
    docker run --rm -v agentsys_chroma_data:/data -v "$PWD/$BACKUP_DIR":/backup alpine tar xzf "/backup/chroma_${BACKUP_PREFIX}.tar.gz" -C /data
    
    # 重启ChromaDB
    docker-compose start chromadb
    
    echo -e "${GREEN}✓${NC} ChromaDB 恢复完成"
else
    echo -e "${RED}✗${NC} ChromaDB 备份文件不存在: $CHROMA_FILE"
fi

# 恢复Redis
if [ -f "$REDIS_FILE" ]; then
    echo -e "${YELLOW}正在恢复 Redis...${NC}"
    
    docker-compose stop redis
    docker cp "$REDIS_FILE" agentsys-redis:/data/dump.rdb
    docker-compose start redis
    
    echo -e "${GREEN}✓${NC} Redis 恢复完成"
else
    echo -e "${YELLOW}⚠${NC} Redis 备份文件不存在: $REDIS_FILE (跳过)"
fi

echo ""
echo "========================================"
echo "  恢复完成"
echo "========================================"
echo ""
echo "正在重启服务..."
docker-compose restart

echo ""
echo -e "${GREEN}✓ 数据恢复完成${NC}"
echo ""
echo "请检查服务状态:"
echo "  docker-compose ps"
echo "  docker-compose logs"

