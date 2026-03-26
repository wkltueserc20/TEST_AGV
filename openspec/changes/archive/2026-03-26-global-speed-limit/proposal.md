## Why

目前系統的速度限制（`max_rpm`）是針對單一 AGV 進行設定的，且只有在選中特定 AGV 時才會顯示在側邊欄下方。這使得操作多台車輛時不夠直觀且效率低下。使用者需要一個全域的控制項，能夠一鍵限制所有 AGV 的最大旋轉速度，並將此設定移至更顯眼的系統控制區塊。

## What Changes

- **新增全域速度控制指令**：在後端 `main.py` 實作 `set_all_speeds` 指令，用於一次更新所有 AGV 的 `max_rpm`。
- **UI 佈局調整**：將速度限制滑桿從「選中車輛設定」區塊移至左側側邊欄頂部的「系統控制（System Control）」區塊。
- **持久化支援**：確保全域設定變動後能正確觸發 `agvs.json` 的更新。

## Capabilities

### New Capabilities
- `global-speed-limit`: 實作一個全域指令與介面，用於控制整個車隊的速度上限。

### Modified Capabilities

## Impact

- **後端 (`main.py`)**: 增加新的指令處理邏輯。
- **前端 (`App.tsx`)**: 修改側邊欄的組件結構與狀態管理。
