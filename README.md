# 兩輪差速 AGV 路徑規劃模擬器 (V2 Pro 版)

這是一個高效、流暢且具備智慧避障能力的 AGV (Automated Guided Vehicle) 模擬系統。採用 **Python FastAPI** 作為運算後端，配合 **React (TypeScript)** 作為可視化前端，實作了工業級的 **DWA (Dynamic Window Approach)** 局部路徑規劃演算法。

![AGV Simulation](https://img.shields.io/badge/Version-2.0-blue)
![Tech Stack](https://img.shields.io/badge/FastAPI-NumPy-green)
![Tech Stack](https://img.shields.io/badge/React-TypeScript-blue)

## 🚀 核心特色

### 1. 絲滑的預測渲染 (Predictive Rendering)
採用 **航位推算 (Dead Reckoning)** 技術。前端不再單純依賴後端傳來的座標繪圖，而是根據速度向量即時推算每一幀的位置，達成絲綢般流暢的 60FPS 動畫效果，完全消除網路延遲造成的跳動感。

### 2. 高效雙執行緒架構 (Multi-threaded Backend)
後端將「通訊層」與「物理引擎」完全分離：
- **通訊執行緒**：負責 WebSocket 訊息收發，保證 UI 指令（Start/Pause）零延遲回應。
- **物理執行緒**：獨立運行 DWA 運算與運動學模擬，確保運算壓力不影響連線穩定性。

### 3. 工業級 DWA 避障演算法
- **動態權重切換**：在開闊地帶全速衝刺，在狹窄區域（如 2m 寬門）自動切換至安全模式。
- **智能脫困**：當陷入死胡同或障礙物包圍時，會自動進行「雷達掃描」尋找最空曠的角度並平滑轉向。
- **物理參數**：模擬 1m x 1m 車體，支援高達 3000 RPM (600mm/s) 的運動表現。

## 🛠 技術棧

- **後端 (Backend)**: 
  - Python 3.13+
  - **FastAPI / Uvicorn**: 非同步 Web 服務與 WebSockets 通訊。
  - **NumPy**: 高效矩陣運算。
  - **Shapely**: 精確的幾何碰撞偵測。
- **前端 (Frontend)**:
  - React 18 / Vite / TypeScript
  - **HTML5 Canvas**: 50m x 50m 大地圖即時繪製。
  - **WebSocket**: 雙向實時數據同步。

## 📋 系統規格

- **地圖尺寸**: 50,000mm x 50,000mm (50m x 50m)。
- **座標系統**: 笛卡兒座標系 (左下角為 0,0)。
- **AGV 尺寸**: 1,000mm x 1,000mm。
- **速度上限**: 3000 RPM (約 600 mm/s)。
- **模擬倍率**: 支援 10x ~ 50x 加速預覽 (預設穩定值為 15x)。

## ⚙️ 安裝與啟動

### 1. 下載專案
```bash
git clone <your-repo-url>
cd <project-folder>
```

### 2. 快速啟動 (Windows)
專案內建了一鍵啟動腳本：
```powershell
.\start.ps1
```
*這會自動初始化後端 Python 環境與前端依賴，並開啟兩個視窗運行服務。*

### 3. 手動啟動
**後端**:
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install fastapi uvicorn numpy shapely websockets
python main.py
```
**前端**:
```bash
cd frontend
npm install
npm run dev
```

## 🎮 操作說明

- **左鍵點擊**: 在地圖上新增障礙物 (預設 1m x 1m 正方形)。
- **右鍵點擊**: 設定 AGV 的 **目標 B 點**。
- **側邊欄管理**:
  - 調整 **Speed Limit**：即時改變馬達極限轉速。
  - **座標編輯**：直接輸入數值精確移動障礙物位置。
  - **即時遙測**：查看實時 X, Y, V, ω, RPM 等數值。
- **Delete 鍵**: 刪除選中的障礙物。

---

## 📄 專案結構

```text
├── backend/
│   ├── main.py         # FastAPI 伺服器與雙執行緒調度
│   ├── dwa.py          # DWA 避障演算法核心
│   ├── kinematics.py   # 兩輪差速運動學模型
│   └── venv/           # Python 虛擬環境
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # UI 佈局與狀態管理
│   │   ├── SimulatorCanvas.tsx # 60FPS 預測渲染畫布
│   │   └── useSimulation.ts    # WebSocket 客戶端 Hook
│   └── ...
└── start.ps1           # 一鍵啟動腳本
```
