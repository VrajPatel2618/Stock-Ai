@echo off
echo ============================================
echo   Stock.AI - Starting Application
echo ============================================

echo [1/2] Starting Django backend on port 8000...
start "Stock.AI Backend" cmd /k "python manage.py runserver 8000"

timeout /t 2 /nobreak >nul

echo [2/2] Starting React frontend on port 5173...
start "Stock.AI Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo   App running at: http://localhost:5173
echo   API running at: http://localhost:8000/api
echo ============================================
start http://localhost:5173
