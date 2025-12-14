@echo off
echo ========================================
echo Factory Safety Detection System
echo FastAPI Backend Server
echo ========================================
echo.
echo Starting server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

cd backend
python -m app.main

pause
