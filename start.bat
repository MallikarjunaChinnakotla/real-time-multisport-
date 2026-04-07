@echo off
title Real-Time Multi-Sport Dashboard - Launcher
color 0A
echo ============================================================
echo     Real-Time Multi-Sport Dashboard - Starting...
echo ============================================================
echo.

:: Start FastAPI backend in a new terminal window
echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "Multi-Sport Backend (FastAPI)" cmd /k "cd /d %~dp0backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Small delay to let backend start first
timeout /t 2 /nobreak >nul

:: Start React frontend dev server
echo [2/2] Starting React Frontend on http://localhost:5173 ...
start "Multi-Sport Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ------------------------------------------------------------
echo  Backend  : http://localhost:8000
echo  API Docs : http://localhost:8000/docs
echo  Frontend : http://localhost:5173
echo ------------------------------------------------------------
echo.
echo Both services are starting in separate windows.
echo Close those windows to stop the servers.
echo.
pause
