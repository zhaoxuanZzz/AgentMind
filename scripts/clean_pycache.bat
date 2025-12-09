@echo off
REM ========================================
REM 清理 Python 缓存文件
REM ========================================

echo.
echo ======================================
echo   清理 Python __pycache__ 目录
echo ======================================
echo.

cd /d "%~dp0\.."

echo 正在查找 __pycache__ 目录...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo 删除: %%d
        rmdir /s /q "%%d"
    )
)

echo.
echo 正在查找 .pyc 文件...
for /r %%f in (*.pyc) do (
    if exist "%%f" (
        echo 删除: %%f
        del /q "%%f"
    )
)

echo.
echo ======================================
echo   清理完成！
echo ======================================
echo.

pause

