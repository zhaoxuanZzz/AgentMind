@echo off
REM ========================================
REM Backend Development Server Launcher
REM ========================================

echo.
echo ======================================
echo   Starting Backend Server
echo ======================================
echo.

REM Switch to backend directory
cd /d "%~dp0"

REM Activate virtual environment (supports venv and conda)
echo [1/3] Activating virtual environment...

REM Check for conda environment
conda info --envs >nul 2>&1
if %errorlevel% equ 0 (
    REM conda available, try to activate environment
    echo Detected conda, trying to activate environment...
    call conda activate agentSys 2>nul
    if %errorlevel% neq 0 (
        call conda activate agentsys 2>nul
        if %errorlevel% neq 0 (
            echo Warning: agentsys/agentSys environment not found, using current environment...
        )
    )
) else if exist venv\Scripts\activate.bat (
    REM Use venv
    echo Using venv virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found
    echo.
    echo Please create a virtual environment:
    echo   1. Using conda: conda create -n agentsys python=3.11
    echo   2. Using venv: python -m venv venv
    echo.
    pause
    exit /b 1
)

REM Check .env file
if not exist .env (
    echo WARNING: .env file not found
    if exist ..\env.template (
        echo Creating .env file from template...
        copy ..\env.template .env >nul
        echo.
        echo .env file created. Please configure:
        echo   - DASHSCOPE_API_KEY: Alibaba DashScope API Key
        echo   - SECRET_KEY: Random secret key for JWT
        echo.
        notepad .env
        echo.
        echo Please re-run this script after configuration
        pause
        exit /b 1
    ) else (
        echo ERROR: env.template not found
        pause
        exit /b 1
    )
)

echo.
echo [2/3] Checking dependencies...
python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Dependencies not installed, installing...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo [3/3] Starting server...

REM Set PYTHONPATH (Important!)
set PYTHONPATH=%CD%
echo Setting PYTHONPATH=%CD%

echo.
echo ======================================
echo   Server Information
echo ======================================
echo   - API URL: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Working Dir: %CD%
echo   - PYTHONPATH: %PYTHONPATH%
echo ======================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server (using python -m to ensure correct environment)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
