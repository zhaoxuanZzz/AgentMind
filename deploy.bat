@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Agent System 一键部署脚本 (Windows)

echo ================================================
echo   Agent System - 一键部署脚本 (Windows)
echo ================================================
echo.

REM 检查 Docker 是否安装
echo 1. 检查系统依赖...
docker --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到 Docker，请先安装 Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo √ Docker 已安装

REM 检查 Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo 错误: 未检测到 docker-compose
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE=docker compose
) else (
    set DOCKER_COMPOSE=docker-compose
)
echo √ Docker Compose 已安装

REM 检查 .env 文件
echo.
echo 2. 检查配置文件...
if not exist .env (
    echo 警告: .env 文件不存在，将从 .env.example 复制
    if exist .env.example (
        copy .env.example .env >nul
        echo 警告: 请编辑 .env 文件，配置 OPENAI_API_KEY 等必要参数
        echo.
        set /p answer="是否现在编辑 .env 文件? (y/n): "
        if /i "!answer!"=="y" (
            notepad .env
        ) else (
            echo 警告: 请手动编辑 .env 文件后再运行部署脚本
            pause
            exit /b 0
        )
    ) else (
        echo 错误: .env.example 文件不存在
        pause
        exit /b 1
    )
)

REM 检查 OPENAI_API_KEY
findstr /C:"your-api-key-here" .env >nul
if not errorlevel 1 (
    echo 错误: 请先在 .env 文件中配置 OPENAI_API_KEY
    pause
    exit /b 1
)
echo √ 配置文件检查完成

REM 停止并删除旧容器
echo.
echo 3. 清理旧容器...
%DOCKER_COMPOSE% down --remove-orphans >nul 2>&1
echo √ 旧容器清理完成

REM 构建镜像
echo.
echo 4. 构建 Docker 镜像...
echo    这可能需要几分钟时间，请耐心等待...
%DOCKER_COMPOSE% build --no-cache
if errorlevel 1 (
    echo 错误: 镜像构建失败
    pause
    exit /b 1
)
echo √ 镜像构建完成

REM 启动服务
echo.
echo 5. 启动服务...
%DOCKER_COMPOSE% up -d
if errorlevel 1 (
    echo 错误: 服务启动失败
    pause
    exit /b 1
)
echo √ 服务启动完成

REM 等待服务就绪
echo.
echo 6. 等待服务就绪...
echo    这可能需要几分钟时间，请耐心等待...

REM 等待后端服务（最多等待120秒）
set /a count=0
:wait_backend
timeout /t 2 /nobreak >nul
set /a count+=1
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    if !count! lss 60 (
        echo|set /p=.
        goto wait_backend
    ) else (
        echo.
        echo 错误: 后端服务启动超时
        pause
        exit /b 1
    )
)
echo.
echo √ 后端服务已就绪

REM 等待前端服务
set /a count=0
:wait_frontend
timeout /t 2 /nobreak >nul
set /a count+=1
curl -f http://localhost:8080 >nul 2>&1
if errorlevel 1 (
    if !count! lss 60 (
        echo|set /p=.
        goto wait_frontend
    ) else (
        echo.
        echo 错误: 前端服务启动超时
        pause
        exit /b 1
    )
)
echo.
echo √ 前端服务已就绪

echo.
echo ================================================
echo 部署成功！
echo ================================================
echo.
echo 服务访问地址:
echo   - 前端界面: http://localhost:8080
echo   - 后端API:  http://localhost:8000
echo   - API文档:  http://localhost:8000/docs
echo.
echo 数据库连接信息:
echo   - PostgreSQL: localhost:5432
echo   - Redis:      localhost:6379
echo   - ChromaDB:   localhost:8001
echo.
echo 常用命令:
echo   查看日志:   %DOCKER_COMPOSE% logs -f
echo   停止服务:   %DOCKER_COMPOSE% stop
echo   启动服务:   %DOCKER_COMPOSE% start
echo   重启服务:   %DOCKER_COMPOSE% restart
echo   删除服务:   %DOCKER_COMPOSE% down
echo.
echo ================================================
echo.
pause

