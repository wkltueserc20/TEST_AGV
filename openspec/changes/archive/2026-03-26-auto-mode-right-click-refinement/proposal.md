## Why

在目前的模擬器中，`AUTO` 模式的右鍵行為僅限於取消目前正在指派的任務起點（`CANCEL_TASK`）。使用者希望在 `AUTO` 模式下右鍵點擊時，除了取消任務起點外，也能同時清除目前選中的 AGV 或物件，這能提供更一致的互動體驗（與 `SELECT` 模式類似）。

## What Changes

- 修改 `App.tsx` 中的 `onCanvasRightClick` 邏輯。
- 當處於 `AUTO` 模式（對應 `perm === 'CANCEL_TASK'`）並點擊右鍵時，系統將會：
    1. 呼叫 `setAutoTaskSource(null)` 以重置任務指派狀態。
    2. 呼叫 `setSelectedAgvId(null)` 以清除選中的 AGV。
    3. 呼叫 `setSelectedObId(null)` 以清除選中的物件。

## Capabilities

### New Capabilities
- `auto-mode-full-reset`: 擴展 `AUTO` 模式右鍵的功能，實現一鍵重置所有選取狀態。

### Modified Capabilities

## Impact

- **前端 (`App.tsx`)**: 僅修改右鍵點擊事件的處理邏輯。
