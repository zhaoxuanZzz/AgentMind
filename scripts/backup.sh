#!/bin/bash

# Agent System 数据备份脚本

set -e

# 备份目录
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "  Agent System 数据备份"
echo "========================================"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

echo "备份目录: $BACKUP_DIR"
echo "备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 备份PostgreSQL
echo -e "${YELLOW}正在备份 PostgreSQL...${NC}"
docker exec agentsys-postgres pg_dump -U agentsys agentsys | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"
POSTGRES_SIZE=$(ls -lh "$BACKUP_DIR/postgres_$DATE.sql.gz" | awk '{print $5}')
echo -e "${GREEN}✓${NC} PostgreSQL 备份完成 (大小: $POSTGRES_SIZE)"

# 备份ChromaDB
echo -e "${YELLOW}正在备份 ChromaDB...${NC}"
docker run --rm -v agentsys_chroma_data:/data -v "$PWD/$BACKUP_DIR":/backup alpine tar czf "/backup/chroma_$DATE.tar.gz" -C /data .
CHROMA_SIZE=$(ls -lh "$BACKUP_DIR/chroma_$DATE.tar.gz" | awk '{print $5}')
echo -e "${GREEN}✓${NC} ChromaDB 备份完成 (大小: $CHROMA_SIZE)"

# 备份Redis（可选）
echo -e "${YELLOW}正在备份 Redis...${NC}"
docker exec agentsys-redis redis-cli --rdb /data/dump.rdb > /dev/null 2>&1
docker cp agentsys-redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"
REDIS_SIZE=$(ls -lh "$BACKUP_DIR/redis_$DATE.rdb" | awk '{print $5}')
echo -e "${GREEN}✓${NC} Redis 备份完成 (大小: $REDIS_SIZE)"

echo ""
echo "========================================"
echo "  备份完成"
echo "========================================"
echo ""
echo "备份文件:"
echo "  - $BACKUP_DIR/postgres_$DATE.sql.gz"
echo "  - $BACKUP_DIR/chroma_$DATE.tar.gz"
echo "  - $BACKUP_DIR/redis_$DATE.rdb"
echo ""

# 清理旧备份（保留最近30天）
RETENTION_DAYS=30
echo "正在清理 $RETENTION_DAYS 天前的旧备份..."
find "$BACKUP_DIR" -name "*.gz" -o -name "*.rdb" | while read file; do
    if [ $(find "$file" -mtime +$RETENTION_DAYS 2>/dev/null | wc -l) -gt 0 ]; then
        rm -f "$file"
        echo "已删除: $(basename $file)"
    fi
done

echo ""
echo -e "${GREEN}✓ 备份流程完成${NC}"

