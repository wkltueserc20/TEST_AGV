# Tasks: AGV DWA Simulator Implementation

## Step 1: Backend (Python FastAPI) Setup
- [x] 初始化 Python 虛擬環境並安裝 FastAPI, Uvicorn, NumPy, Shapely.
- [x] 實作基礎 WebSocket 服務端框架。
- [x] 實作 AGV 差速運動學模型類 (Kinematics).
- [x] 實作 DWA 演算法核心模組 (Dynamic Window Search).
- [x] 實作圓形與矩形障礙物的碰撞檢測邏輯.

## Step 2: Frontend (React) Setup
- [x] 初始化 Vite + React (TypeScript) 專案。
- [x] 實作 WebSocket 客戶端與狀態管理。
- [x] 建立 HTML5 Canvas 繪圖組件 (支援坐標系轉換)。
- [x] 實作 AGV 1m x 1m 車體繪製、目標 B 點繪製.

## Step 3: Interaction & Management
- [x] 實作畫布點擊事件（新增圓形/矩形障礙物）。
- [x] 實作障礙物選中與 Delete 鍵刪除功能。
- [x] 實作側邊欄 (Sidebar) 的障礙物列表管理與實時遙測儀表。

## Step 4: Simulation & Refinement
- [x] 串聯前後端，驗證 A 點到 B 點的自動尋跡。
- [x] 調整 DWA 評分參數，確保避障平滑且不撞到 1m x 1m 的車體角落。
- [x] 實作 RPM 的數值顯示與差速 (Differential) 的回饋顯示。

## Step 5: Final Review & Polish
- [x] 檢查坐標系是否正確 (左下角 0,0)。
- [x] 優化 UI 樣式，增加地圖格線 (Grid)。
