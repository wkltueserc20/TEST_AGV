## Context

目前系統透過 `multiplier` 實現加速模擬，但在 `telemetry` 中並未包含時間維度的數據。這使得評估 AGV 運作效率變得困難。我們需要將物理引擎中的時間步長與模擬倍率結合，計算出「模擬世界」的時間。

## Goals / Non-Goals

**Goals:**
- 在後端實現模擬時間的累加（Simulation Time Integration）。
- 持久化記錄 AGV 的當前與歷史任務耗時。
- 前端能以 `xxx分xx秒` 格式展示時間。

**Non-Goals:**
- 不改變物理引擎的步長（維持 0.05s 或 0.1s），僅改變對應的模擬時間增加量。
- 不實作跨 Session 的時間持久化（重啟後計時器歸零是可接受的，除非是已存在的 agvs.json 機制）。

## Decisions

### 1. 後端模擬時間累算
在 `main.py` 的物理引擎循環中，原本就有 `sim_dt = real_dt * SIM_MULTIPLIER`。我們將此 `sim_dt` 傳遞給 `AGV.update` 方法。
在 `AGV.update` 中：
- 如果 `self.is_running` 為真，則 `self.current_travel_time += dt`。
- 當狀態從 `EXECUTING/LOADING/UNLOADING` 切換回 `IDLE` 時，將 `current_travel_time` 賦值給 `last_travel_time` 並歸零 `current_travel_time`。

### 2. 任務對象與時間關聯
在 `world.py` 中：
- `Task` 物件將新增 `execution_time` 欄位。
- 在 `complete_task` 時，從執行該任務的 AGV 中提取 `current_travel_time` 並存入任務歷史。

### 3. 前端格式化與顯示
- 在 `App.tsx` 中新增一個 `formatSimTime` 函式。
- 修改 `fleet-list` 的渲染，將時間嵌入 ID 旁邊。
- 修改 `task-history` 與 `task-queue` 的渲染邏輯。

## Risks / Trade-offs

- **[Risk] 精度誤差**：累積的時間積分可能隨時間產生微小漂移。
  - **Mitigation**: 由於是模擬器，微秒級誤差不影響使用者體驗。
- **[Trade-off] 效能影響**：每幀增加一次加法運算。
  - **Result**: 極輕量，對整體效能無影響。

## Open Questions
- 當任務被「強制停止 (Force Idle)」時，計時器是否應該立即結算到 `last_travel_time`？（決策：是的，應該記錄到停止那一刻的時間）。
