#!/bin/bash

# Agent System 健康检查脚本

set -e

echo "========================================"
echo "  Agent System 健康检查"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查计数
TOTAL=0
PASSED=0
FAILED=0

check_service() {
    local url=$1
    local name=$2
    TOTAL=$((TOTAL + 1))
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name 运行正常"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $name 无法访问"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

check_container() {
    local container=$1
    local name=$2
    TOTAL=$((TOTAL + 1))
    
    if docker ps | grep -q "$container"; then
        echo -e "${GREEN}✓${NC} $name 容器运行中"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $name 容器未运行"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "1. 检查容器状态..."
check_container "agentsys-postgres" "PostgreSQL数据库"
check_container "agentsys-redis" "Redis缓存"
check_container "agentsys-chromadb" "ChromaDB向量库"
check_container "agentsys-backend" "后端API服务"
check_container "agentsys-frontend" "前端Web服务"

echo ""
echo "2. 检查服务端点..."
check_service "http://localhost:8000/health" "后端健康检查"
check_service "http://localhost:8000" "后端根路径"
check_service "http://localhost:8080" "前端服务"

echo ""
echo "3. 检查数据库连接..."
TOTAL=$((TOTAL + 1))
if docker exec agentsys-postgres pg_isready -U agentsys > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL连接正常"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} PostgreSQL连接失败"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "4. 检查Redis连接..."
TOTAL=$((TOTAL + 1))
if docker exec agentsys-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis连接正常"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Redis连接失败"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "========================================"
echo "  检查结果汇总"
echo "========================================"
echo ""
echo "总计: $TOTAL 项"
echo -e "${GREEN}通过: $PASSED 项${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}失败: $FAILED 项${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！系统运行正常。${NC}"
    echo ""
    echo "访问地址:"
    echo "  前端: http://localhost:8080"
    echo "  后端: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    exit 0
else
    echo -e "${RED}✗ 发现问题，请查看失败项并进行修复。${NC}"
    echo ""
    echo "常用命令:"
    echo "  查看日志: docker-compose logs -f"
    echo "  重启服务: docker-compose restart"
    exit 1
fi

