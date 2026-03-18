# AGV Simulator 一鍵啟動腳本

Write-Host "正在啟動 AGV 模擬器..." -ForegroundColor Cyan

# 1. 啟動後端 (Python FastAPI)
Write-Host "啟動後端服務 (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\python main.py"

# 2. 啟動前端 (React Vite)
Write-Host "啟動前端介面 (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "啟動完成！請開啟瀏覽器訪問 http://localhost:5173" -ForegroundColor Green
