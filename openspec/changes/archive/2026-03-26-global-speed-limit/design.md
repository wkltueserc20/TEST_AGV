## Context

目前的速度限制邏輯高度耦合於 `selectedAgvId` 狀態。當使用者想要調整模擬整體的運行速度上限時，需要逐一選取車輛，這非常不直觀。我們需要將此控制項提昇為全域屬性。

## Goals / Non-Goals

**Goals:**
- 提供一個全域滑桿來設定所有 AGV 的 `max_rpm`。
- 將設定項移至側邊欄的最顯眼位置。
- 實作後端的批次更新邏輯。

**Non-Goals:**
- 不改變 AGV 內部的物理控制邏輯。
- 不刪除單機設定的底層指令支援，但 UI 上僅保留全域入口。

## Decisions

### 1. 後端指令實作 (main.py)
在 `backend/main.py` 的指令處理迴圈中，新增一個處理分支：
```python
elif t == "set_all_speeds":
    new_speed = float(msg.get("data", 3000))
    with world_lock:
        for agv in world.agvs.values():
            agv.max_rpm = new_speed
        world.save_agvs() # 確保持久化
```

### 2. 前端狀態管理與 UI (App.tsx)
- **狀態提昇**：在 `App` 組件中新增一個 `globalRpm` 狀態（初始值設為 3000）。
- **位置變更**：在左側側邊欄的「System Control」區塊下方新增一個 `section`。
- **組件實作**：使用 `input type="range"` 配合 `label` 顯示數值。

### 3. 持久化與同步
當全域速度改變時，前端發送 `set_all_speeds` 指令。後端更新記憶體中的 AGV 實體，並觸發 `save_agvs()`。這樣下次重新啟動後，所有 AGV 都會繼承最後一次設定的數值。

## Risks / Trade-offs

- **[Risk] 設定被覆蓋**：如果使用者習慣了單機設定，全域設定會一次性覆蓋所有數值。
  - **Mitigation**: 這被視為預期行為，簡化了複雜度。
- **[Trade-off] 前後端數值同步**：初始啟動時，前端的 `globalRpm` 可能與後端真實值不一致。
  - **Result**: 可以透過在 `telemetry` 中回傳一個代表當前基準速度的值，或者簡單地讓使用者拉動一次滑桿來同步。
