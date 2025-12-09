# Agent System Makefile
# 提供常用操作的快捷命令

.PHONY: help setup build up down restart logs clean test

help: ## 显示帮助信息
	@echo "Agent System - 可用命令:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## 初始化配置（首次使用）
	@echo "正在初始化配置..."
	@if [ ! -f .env ]; then \
		cp env.template .env; \
		echo "✓ 已创建 .env 文件"; \
		echo "⚠ 请编辑 .env 文件，配置 OPENAI_API_KEY"; \
	else \
		echo "✓ .env 文件已存在"; \
	fi
	@chmod +x deploy.sh

build: ## 构建Docker镜像
	@echo "正在构建镜像..."
	docker-compose build

up: ## 启动所有服务
	@echo "正在启动服务..."
	docker-compose up -d
	@echo "✓ 服务已启动"
	@echo "  前端: http://localhost:8080"
	@echo "  后端: http://localhost:8000"
	@echo "  API文档: http://localhost:8000/docs"

down: ## 停止并删除所有服务
	@echo "正在停止服务..."
	docker-compose down

stop: ## 停止服务（不删除）
	@echo "正在停止服务..."
	docker-compose stop

start: ## 启动已停止的服务
	@echo "正在启动服务..."
	docker-compose start

restart: ## 重启所有服务
	@echo "正在重启服务..."
	docker-compose restart

logs: ## 查看所有服务日志
	docker-compose logs -f

logs-backend: ## 查看后端日志
	docker-compose logs -f backend

logs-frontend: ## 查看前端日志
	docker-compose logs -f frontend

ps: ## 查看服务状态
	docker-compose ps

clean: ## 清理所有容器和数据（危险操作！）
	@echo "⚠️  警告：此操作将删除所有数据！"
	@read -p "确定要继续吗？(y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "✓ 已清理所有容器和数据"; \
	fi

backup: ## 备份数据库
	@echo "正在备份数据库..."
	@mkdir -p backups
	@docker exec agentsys-postgres pg_dump -U agentsys agentsys | gzip > backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "✓ 备份完成"

shell-backend: ## 进入后端容器shell
	docker exec -it agentsys-backend /bin/bash

shell-db: ## 进入数据库shell
	docker exec -it agentsys-postgres psql -U agentsys

test: ## 运行测试（TODO）
	@echo "测试功能即将推出..."

install-dev: ## 安装开发依赖
	@echo "正在安装后端开发依赖..."
	cd backend && pip install -r requirements.txt
	@echo "正在安装前端开发依赖..."
	cd frontend && npm install

dev-backend: ## 运行后端开发服务器
	cd backend && python -m app.main

dev-frontend: ## 运行前端开发服务器
	cd frontend && npm run dev

update: ## 更新并重新部署
	@echo "正在更新..."
	git pull
	docker-compose build
	docker-compose up -d
	@echo "✓ 更新完成"

