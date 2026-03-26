## Why

為了提升 AGV 模擬系統的專業度與效率評估能力，我們需要引入「模擬時間」追蹤功能。目前系統雖支援加速模擬（1x~30x），但使用者無法直觀得知在特定倍率下任務實際耗費的「模擬時間」。此功能將幫助使用者評估物流動線效率，並清晰記錄每趟任務的執行表現。

## What Changes

- **後端時間積分系統**：在物理引擎中實作受模擬倍率影響的時間累加邏輯。
- **AGV 狀態擴充**：為 AGV 實體新增 `current_travel_time` (當前行走時間) 與 `last_travel_time` (上一次行走時間) 屬性。
- **任務對象擴充**：在任務隊列與任務歷史中紀錄並傳回執行所耗費的模擬時間。
- **前端 UI 增強**：
    - 在 Fleet Status 中，AGV ID 旁即時顯示當前行走時間，卡片下方顯示上一次行走紀錄。
    - 在任務隊列（Task Queue）中顯示正在執行任務的累計時間。
    - 在任務歷史（Task History）中顯示完成任務的總耗時。
- **時間格式化**：前端實作 `xxx分xx秒` 的格式化工具。

## Capabilities

### New Capabilities
- `simulation-time-integration`: 後端根據實時計時與倍率計算模擬時間的邏輯。
- `travel-history-persistence`: 追蹤並保存 AGV 上一次任務的執行時間。
- `simulation-timer-ui`: 前端顯示格式化模擬時間的組件與邏輯。

### Modified Capabilities

## Impact

- **後端 (`agv.py`, `world.py`, `main.py`)**: 影響 AGV 的 state dictionary 結構，增加時間更新邏輯。
- **前端 (`App.tsx`)**: 影響 Sidebar 的 Fleet Status 與 Task 列表的渲染邏輯。
