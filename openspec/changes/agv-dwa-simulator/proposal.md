# Proposal: 2-Wheel Differential AGV Path Simulator (DWA)

## 1. Overview
這是一個模擬兩輪差速驅動 AGV 路徑規劃與避障的專案。透過 React 與 Python (FastAPI)，模擬一個 1m x 1m 的車體在 50m x 50m 的場景中從 A 點移動到 B 點，並能自動避開使用者新增的圓形與矩形障礙物。

## 2. Core Specifications
*   **AGV Type**: 2-Wheel Differential Drive (兩輪差速驅動)
*   **AGV Size**: 1000mm x 1000mm (Square)
*   **Max Speed**: 3000 RPM (約等於 600 mm/s)
*   **Algorithm**: Dynamic Window Approach (DWA) 局部路徑規劃器
*   **Coordinate System**: 笛卡兒坐標系 (Cartesian)，左下角為 (0,0)，X 向右，Y 向上。
*   **Obstacles**: 支援圓形 (Circle) 與矩形 (Rectangle) 的新增與刪除。

## 3. Key Features
*   **Real-time Simulation**: 實時回饋 AGV 的座標 (x, y, theta)、左右輪 RPM、差速。
*   **Interactive UI**: 
    *   在 Canvas 上點擊新增圓形或矩形障礙物。
    *   選中障礙物後可按 Delete 鍵刪除。
    *   側邊欄提供障礙物管理列表與 AGV 狀態儀表板。
*   **Backend Logic**: Python 處理 DWA 運算，透過 WebSockets 傳輸每幀的座標與速度數據。

## 4. Tech Stack
*   **Frontend**: React (TypeScript), HTML5 Canvas, Socket.io-client / WebSocket.
*   **Backend**: Python (FastAPI), WebSockets, NumPy (矩陣運算), Shapely (幾何碰撞檢測).

## 5. Success Criteria
*   AGV 能夠平滑地從點 A 移動到點 B，且不碰撞任何圓形或矩形障礙物。
*   前端儀表板能即時、準確地顯示 RPM 與坐標數據。
*   障礙物的新增與刪除功能運作正常，且後端能同步更新環境地圖。
