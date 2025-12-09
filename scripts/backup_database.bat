@echo off
REM ============================================
REM Agent System 数据库备份脚本 (Windows)
REM ============================================
REM 说明：本脚本用于备份PostgreSQL数据库
REM 支持Docker和本地PostgreSQL两种方式
REM ============================================

setlocal enabledelayedexpansion

REM 默认配置
if "%DB_NAME%"=="" set DB_NAME=agentsys
if "%DB_USER%"=="" set DB_USER=agentsys
if "%DB_HOST%"=="" set DB_HOST=localhost
if "%DB_PORT%"=="" set DB_PORT=5432
if "%BACKUP_DIR%"=="" set BACKUP_DIR=.\backups
if "%USE_DOCKER%"=="" set USE_DOCKER=false
if "%DOCKER_CONTAINER%"=="" set DOCKER_CONTAINER=agentsys-postgres

REM 生成备份文件名
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATE=%datetime:~0,8%_%datetime:~8,6%
set BACKUP_FILE=%BACKUP_DIR%\%DB_NAME%_%DATE%.sql
set BACKUP_FILE_GZ=%BACKUP_FILE%.gz

echo ========================================
echo   Agent System 数据库备份
echo ========================================
echo.
echo 数据库配置:
echo   数据库名: %DB_NAME%
echo   用户名: %DB_USER%
echo   主机: %DB_HOST%
echo   端口: %DB_PORT%
echo   备份目录: %BACKUP_DIR%
echo   使用Docker: %USE_DOCKER%
if "%USE_DOCKER%"=="true" (
    echo   Docker容器: %DOCKER_CONTAINER%
)
echo.

REM 创建备份目录
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 执行备份
echo 正在备份数据库...

if "%USE_DOCKER%"=="true" (
    REM Docker方式备份
    docker ps | findstr "%DOCKER_CONTAINER%" >nul
    if errorlevel 1 (
        echo 错误: Docker容器 %DOCKER_CONTAINER% 未运行
        exit /b 1
    )
    
    docker exec %DOCKER_CONTAINER% pg_dump -U %DB_USER% %DB_NAME% | gzip > "%BACKUP_FILE_GZ%"
) else (
    REM 本地PostgreSQL备份
    REM 检查pg_dump是否可用
    where pg_dump >nul 2>&1
    if errorlevel 1 (
        echo 错误: 未找到 pg_dump 命令，请安装PostgreSQL客户端
        exit /b 1
    )
    
    REM 执行备份（需要设置PGPASSWORD环境变量）
    if not "%PGPASSWORD%"=="" (
        set PGPASSWORD=%PGPASSWORD%
    )
    
    REM 尝试使用自定义格式，如果失败则使用SQL格式
    pg_dump -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -F c -f "%BACKUP_FILE%" 2>nul
    if errorlevel 1 (
        pg_dump -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% > "%BACKUP_FILE%"
    )
)

REM 检查备份是否成功
if exist "%BACKUP_FILE_GZ%" (
    echo [成功] 数据库备份完成
    echo   备份文件: %BACKUP_FILE_GZ%
    for %%A in ("%BACKUP_FILE_GZ%") do echo   文件大小: %%~zA 字节
) else if exist "%BACKUP_FILE%" (
    echo [成功] 数据库备份完成
    echo   备份文件: %BACKUP_FILE%
    for %%A in ("%BACKUP_FILE%") do echo   文件大小: %%~zA 字节
) else (
    echo [失败] 备份失败：备份文件未生成
    exit /b 1
)

echo.
echo ========================================
echo   备份完成
echo ========================================
echo.
echo 使用方法:
echo   1. Docker方式: set USE_DOCKER=true ^&^& backup_database.bat
echo   2. 本地方式: set DB_HOST=localhost ^&^& set DB_USER=agentsys ^&^& set DB_NAME=agentsys ^&^& backup_database.bat
echo   3. 自定义目录: set BACKUP_DIR=D:\backups ^&^& backup_database.bat
echo.

