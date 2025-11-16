@echo off
echo =====================================
echo Factory Safety Detector - Quick Start
echo =====================================
echo.

echo Checking if backend is already running...
curl -s http://localhost:8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo Backend is already running on port 8000
) else (
    echo Starting backend server...
    start "Factory Safety Backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --reload --port 8000"
    echo Waiting for backend to initialize...
    timeout /t 5 /nobreak >nul
)

echo.
echo Checking if frontend is already running...
curl -s http://localhost:4200 >nul 2>&1
if %errorlevel% equ 0 (
    echo Frontend is already running on port 4200
) else (
    echo Starting frontend server...
    start "Factory Safety Frontend" cmd /k "cd /d %~dp0frontend && ng serve"
    echo Waiting for frontend to compile...
    timeout /t 10 /nobreak >nul
)

echo.
echo =====================================
echo System Status:
echo =====================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:4200
echo API Docs: http://localhost:8000/docs
echo =====================================
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:4200

echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
