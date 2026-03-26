## Why

目前系統在新增、更新或移除障礙物、AGV 及設備時，會無差別地觸發所有 AGV 的重新規劃（Replan）。這導致處於 `IDLE` 狀態的 AGV 被錯誤地帶入 `PLANNING` 與 `EXECUTING` 狀態，即便它們沒有設定目標或任務。這種狀態異常會導致 `AUTO` 模式的任務指派員（Dispatcher）認為車輛正忙，進而無法正確指派新任務。

## What Changes

- **優化重新規劃觸發邏輯**：在 `backend/main.py` 中，修改環境變動後的 `replan_needed` 設置邏輯，使其僅針對正在運行（`is_running == True`）的 AGV。
- **增強 AGV 狀態機守衛**：在 `backend/agv.py` 的 `update` 方法中，增加對 `_async_replan` 的調用限制，確保只有在 `is_running` 為真且必要時才啟動路徑規劃。
- **防止 IDLE 狀態洩漏**：確保 `IDLE` 車輛在環境變動下維持 `IDLE` 狀態，不進入規劃隊列。

## Capabilities

### New Capabilities
- `selective-replanning`: 根據 AGV 的運行狀態選擇性地觸發路徑重新規劃。

### Modified Capabilities

## Impact

- **後端 (`main.py`, `agv.py`)**: 修改指令處理邏輯與 AGV 更新循環。
- **系統穩定性**: 解決 `AUTO` 模式指派任務卡死的問題，維持正確的 AGV 狀態流轉。
