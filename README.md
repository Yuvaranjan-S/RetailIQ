# 🛒 RetailIQ — AI-Powered Retail Operating & Decision System

> **Smart India Hackathon 2026 — Problem Statement 179**  
> *"AI-Powered Retail Intelligence Platform"*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg?logo=typescript)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com)
[![Tests](https://img.shields.io/badge/Tests-7%20Passed%20(100%25)-success.svg)](#testing)

---

## 🌟 Vision & Innovation

RetailIQ transforms raw physical store observations into continuous autonomous intelligence:

$$\text{SENSE} \longrightarrow \text{UNDERSTAND} \longrightarrow \text{PREDICT} \longrightarrow \text{DECIDE} \longrightarrow \text{ACT} \longrightarrow \text{LEARN}$$

Unlike traditional dashboards that only show static graphs or historical metrics, RetailIQ implements:
1. **Store Digital Twin Engine (`StoreStateTwin`)**: An in-memory, real-time synchronized state model tracking footfall, 2D zone heatmaps, dwell times, queue states, and 15 SKUs of inventory.
2. **Deterministic Mathematical AI (`queue_predictor.py`)**: Real Erlang-C ($M/M/c$) queueing theory modeling queue wait time, probability of waiting, and required servers with mathematical proof.
3. **EMA Demand & Stockout Predictor (`demand_predictor.py`)**: Exponential moving average consumption rate estimator calculating exact stockout ETAs.
4. **Signal Fusion & Next-Best-Action Engine (`signal_fusion.py` & `rule_engine.py`)**: Multi-signal urgency scoring producing explainable, confidence-scored recommendations with evidence citations.
5. **Closed-Loop Action Feedback & Learning (`ActionResult`)**: When managers accept recommendations, actions simulate directly on the digital twin and measure pre/post performance metrics.
6. **Edge-First & Offline Resilience**: Local processing continues uninterrupted during network dropouts; events queue locally and reconcile automatically upon reconnect.

---

## 🏗 System Architecture

```mermaid
graph TD
    subgraph SENSE ["1. Sense Layer (Edge AI / Simulator)"]
        CAM[Cameras / Edge YOLOv8] --> PIPE[Edge Vision Pipeline]
        SIM[Poisson Store Simulator] --> EVT[/api/events/batch]
        PIPE --> EVT
    end

    subgraph TWIN ["2. Understand Layer (Digital Twin)"]
        EVT --> STATE[StoreStateTwin Manager]
        STATE --> SNAP[In-Memory Spatial Twin]
    end

    subgraph AI ["3. Predict & Decide Layer (AI Engine)"]
        SNAP --> MMC[M/M/c Erlang-C Queue Predictor]
        SNAP --> EMA[EMA Demand & Stockout Predictor]
        MMC --> FUSION[Multi-Signal Fusion Engine]
        EMA --> FUSION
        FUSION --> RULES[Explainable Rule Engine]
        RULES --> RECS[Next-Best-Action Engine]
    end

    subgraph ACT ["4. Act & Learn Layer (Command Center)"]
        RECS --> WS[WebSocket Realtime Broadcast]
        WS --> UI[React + Tailwind UI Command Center]
        UI --> ACT_API[Accept / Reject Action]
        ACT_API --> DB[(Database + Learning History)]
        ACT_API --> STATE
    end
```

---

## 🚀 Quick Start (1-Click Run)

### Prerequisites
- Python 3.10+
- Node.js 18+

### Option A: Windows PowerShell (Instant)
```powershell
.\start.ps1
```

### Option B: Linux / macOS / WSL
```bash
chmod +x start.sh
./start.sh
```

### Option C: Manual Start
**Terminal 1 — Backend & Digital Twin:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Store Simulator:**
```bash
cd backend
python ../simulator/store_simulator.py
```

**Terminal 3 — Frontend Command Center:**
```bash
cd frontend
npm run dev
```

---

## 🌐 URLs & Access

| Component | URL | Credentials |
|---|---|---|
| **Frontend Command Center** | [http://localhost:3000](http://localhost:3000) | `admin` / `admin123` |
| **Judge Demo Mode** | [http://localhost:3000/demo](http://localhost:3000/demo) | One-click scenario launcher |
| **FastAPI Swagger Docs** | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) | Full interactive API explorer |
| **WebSocket Realtime Stream** | `ws://localhost:8000/ws/store?store_id=1` | Continuous twin state push |

---

## 🎯 Judge Demonstration Script (5-Minute Walkthrough)

1. **Open Dashboard (`/`)**: Show live KPI cards, interactive 2D store floor map with traffic heatmaps, and checkout queue bars updating via WebSocket.
2. **Navigate to Judge Demo Mode (`/demo`)**:
   - Activate **"Customer Surge"**: Observe footfall jump $2.5\times$ in real-time.
   - Activate **"Multi-Incident (WOW)"**: Observe concurrent surge, queue build-up, and inventory depletion.
3. **Review AI Recommendations**:
   - Notice AI recommendations popping up in real-time with confidence scores (e.g. 96%).
   - Click to expand **Evidence** (e.g., *"Total queue: 11, Max wait: 5.2 min, Closed checkout available: Checkout 3"*).
4. **Take Action (Closed-Loop Demo)**:
   - Click **"Accept & Apply"** on *"Open Checkout 3"*.
   - Watch Checkout 3 immediately switch to OPEN on the store map and queue lengths decrease in real-time!
   - Click **"Accept"** on *"Restock Maggi Noodles"*.
   - Watch inventory levels immediately replenish on the Inventory screen (`/inventory`).
5. **Demonstrate Offline Edge Resilience**:
   - In Demo Mode, click **"Simulate Failure"**.
   - Notice the status bar changes to **OFFLINE MODE (Queued)**.
   - The UI and AI decision engine continue operating locally without internet.
   - Click **"Restore Network"** and watch the sync counter reconcile all buffered events seamlessly.

---

## 🧪 Testing

Run the automated backend test suite:
```bash
cd backend
python -m pytest tests/ -v
```
**Results:** `7 passed (100%)` covering:
- Erlang-C Queue Prediction ($M/M/c$)
- EMA Demand & Stockout Estimation
- Signal Fusion Urgency Scoring
- Deterministic Rule Engine
- Digital Twin State Transitions
- API Authentication & Protected Endpoints
- Scenario Switching & Offline Synchronization

---

## 📐 Mathematical Foundations

### 1. Erlang-C ($M/M/c$) Queueing Theory
Probability a customer must wait:
$$P(\text{Wait}) = C(c, a) = \frac{\frac{a^c}{c!(1 - \rho)}}{\sum_{k=0}^{c-1}\frac{a^k}{k!} + \frac{a^c}{c!(1 - \rho)}}$$
Where:
- $\lambda$ = Arrival rate (customers / min)
- $\mu$ = Service rate per server
- $c$ = Number of open checkouts
- $a = \frac{\lambda}{\mu}$ (traffic intensity)
- $\rho = \frac{\lambda}{c\mu}$ (server utilization)

Expected waiting time in queue:
$$E[W] = \frac{C(c, a)}{c\mu - \lambda}$$

### 2. Exponential Moving Average Demand Rate
$$\text{EMA}_t = \alpha \cdot R_t + (1 - \alpha) \cdot \text{EMA}_{t-1}$$
$$\text{Stockout ETA} = \frac{\text{Current Stock}}{\text{EMA Demand Rate}}$$

---

## 👥 Demo User Accounts

| Role | Username | Password |
|---|---|---|
| **System Administrator** | `admin` | `admin123` |
| **Store Manager** | `manager` | `manager123` |
| **Floor Staff** | `staff1` | `staff123` |
