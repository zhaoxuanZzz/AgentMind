#!/bin/bash

# Agent System 一键部署脚本
# 支持 Linux/macOS/Windows(Git Bash)

set -e

echo "================================================"
echo "  Agent System - 一键部署脚本"
echo "================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 打印错误信息
error() {
    echo -e "${RED}错误: $1${NC}" >&2
    exit 1
}

# 打印成功信息
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 打印警告信息
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 检查必要的依赖
echo "1. 检查系统依赖..."
if ! command_exists docker; then
    error "未检测到 Docker，请先安装 Docker: https://docs.docker.com/get-docker/"
fi
success "Docker 已安装"

if ! command_exists docker-compose; then
    if ! docker compose version >/dev/null 2>&1; then
        error "未检测到 docker-compose，请先安装: https://docs.docker.com/compose/install/"
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi
success "Docker Compose 已安装"

# 检查 .env 文件
echo ""
echo "2. 检查配置文件..."
if [ ! -f .env ]; then
    warning ".env 文件不存在，将从 .env.example 复制"
    if [ -f .env.example ]; then
        cp .env.example .env
        warning "请编辑 .env 文件，配置 OPENAI_API_KEY 等必要参数"
        echo ""
        read -p "是否现在编辑 .env 文件? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vi} .env
        else
            warning "请手动编辑 .env 文件后再运行部署脚本"
            exit 0
        fi
    else
        error ".env.example 文件不存在"
    fi
fi

# 检查 OPENAI_API_KEY 是否配置
if grep -q "your-api-key-here" .env; then
    error "请先在 .env 文件中配置 OPENAI_API_KEY"
fi
success "配置文件检查完成"

# 停止并删除旧容器
echo ""
echo "3. 清理旧容器..."
$DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true
success "旧容器清理完成"

# 构建镜像
echo ""
echo "4. 构建 Docker 镜像..."
$DOCKER_COMPOSE build --no-cache
success "镜像构建完成"

# 启动服务
echo ""
echo "5. 启动服务..."
$DOCKER_COMPOSE up -d
success "服务启动完成"

# 等待服务就绪
echo ""
echo "6. 等待服务就绪..."
echo "   这可能需要几分钟时间，请耐心等待..."

# 等待后端服务
MAX_RETRIES=60
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "后端服务已就绪"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    error "后端服务启动超时"
fi

# 等待前端服务
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8080 >/dev/null 2>&1; then
        success "前端服务已就绪"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    error "前端服务启动超时"
fi

echo ""
echo "================================================"
echo -e "${GREEN}部署成功！${NC}"
echo "================================================"
echo ""
echo "服务访问地址:"
echo "  - 前端界面: http://localhost:8080"
echo "  - 后端API:  http://localhost:8000"
echo "  - API文档:  http://localhost:8000/docs"
echo ""
echo "数据库连接信息:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis:      localhost:6379"
echo "  - ChromaDB:   localhost:8001"
echo ""
echo "常用命令:"
echo "  查看日志:   $DOCKER_COMPOSE logs -f"
echo "  停止服务:   $DOCKER_COMPOSE stop"
echo "  启动服务:   $DOCKER_COMPOSE start"
echo "  重启服务:   $DOCKER_COMPOSE restart"
echo "  删除服务:   $DOCKER_COMPOSE down"
echo ""
echo "================================================"

