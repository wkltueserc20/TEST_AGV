## Why

當前 AGV 系統在路徑規劃失敗時（如被動態障礙物暫時堵住），會直接進入 `STUCK` 或 `WAITING` 狀態，缺乏明確的「被擋道」標示，也沒有自動重試機制。這導致系統穩定性不足，且使用者難以區分「路徑不存在」與「路徑暫時被堵」。

## What Changes

- 在後端 `AGVStatus` 中新增 `BLOCKED` 與 `ERROR` 狀態。
- 實作自動重試邏輯：規劃失敗時進入 `BLOCKED` 並重試最多 3 次，若全失敗則轉為 `ERROR`。
- 更新前端 `SimulatorCanvas`，顯示新狀態的圖示 (Emoji) 與 LED 燈號。
- 在 `AGV` 類別中新增 `retry_count` 以追蹤重試進度。

## Capabilities

### New Capabilities
- `agv-blocked-state-retry`: 定義 AGV 被擋道時的狀態流轉規則與重試行為。

### Modified Capabilities
- `proactive-evasion`: 調整主動避讓失敗後的後續處理邏輯，與新的重試機制整合。

## Impact

- `backend/agv.py`: 核心狀態機與重試邏輯變更。
- `frontend/src/SimulatorCanvas.tsx`: 狀態顯示與 UI 回饋更新。
- `backend/planner.py`: (僅作參考，確認規劃失敗的返回格式)
