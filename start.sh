#!/usr/bin/env bash
# RetailIQ — 1-Click Complete System Starter (Bash / Linux / WSL)

echo -e "\033[36m==========================================================\033[0m"
echo -e "\033[33m   RetailIQ - AI-Powered Retail Operating Platform        \033[0m"
echo -e "\033[36m   Smart India Hackathon 2026 - Problem Statement 179     \033[0m"
echo -e "\033[36m==========================================================\033[0m"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo -e "\033[32m[1/3] Starting Backend API (FastAPI)...\033[0m"
cd "$DIR/backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 3

echo -e "\033[32m[2/3] Starting Store State Simulator...\033[0m"
python ../simulator/store_simulator.py &
SIM_PID=$!

echo -e "\033[32m[3/3] Starting Frontend (Vite)...\033[0m"
cd "$DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo -e "\n\033[33mRetailIQ is now running!\033[0m"
echo -e " - Frontend Dashboard : \033[37mhttp://localhost:3000\033[0m"
echo -e " - Backend Swagger API: \033[37mhttp://localhost:8000/api/docs\033[0m"
echo -e " - Judge Demo Mode    : \033[35mhttp://localhost:3000/demo\033[0m"
echo -e " Login: admin / admin123\n"

trap "kill $BACKEND_PID $SIM_PID $FRONTEND_PID" EXIT
wait
