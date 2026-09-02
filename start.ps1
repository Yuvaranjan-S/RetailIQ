# RetailIQ — 1-Click Complete System Starter (PowerShell)
# Starts Backend (FastAPI), Simulator, and Frontend (Vite)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   RetailIQ - AI-Powered Retail Operating Platform        " -ForegroundColor Yellow
Write-Host "   Smart India Hackathon 2026 - Problem Statement 179     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Check Python and dependencies
Write-Host "[1/3] Starting RetailIQ Backend API..." -ForegroundColor Green
$BackendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru

Start-Sleep -Seconds 3

# 2. Start Simulator
Write-Host "[2/3] Starting Store State Simulator..." -ForegroundColor Green
$SimJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; python ../simulator/store_simulator.py" -PassThru

# 3. Start Frontend
Write-Host "[3/3] Starting Frontend Dev Server..." -ForegroundColor Green
$FrontendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\frontend'; npm run dev" -PassThru

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " RetailIQ is now running!" -ForegroundColor Yellow
Write-Host " - Frontend Dashboard : http://localhost:3000" -ForegroundColor White
Write-Host " - Backend Swagger API: http://localhost:8000/api/docs" -ForegroundColor White
Write-Host " - WebSocket Stream   : ws://localhost:8000/ws/store" -ForegroundColor White
Write-Host " - Judge Demo Mode    : http://localhost:3000/demo" -ForegroundColor Magenta
Write-Host ""
Write-Host " Login with: admin / admin123" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
