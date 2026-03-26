## Context

當前系統在環境發生變化（如 `add_obstacle`, `add_agv` 等）時，會將 `world.agvs` 中所有 AGV 的 `replan_needed` 標記為 `True`。這觸發了 AGV 類別中的 `_async_replan` 方法，該方法會將 AGV 狀態從 `IDLE` 更改為 `PLANNING`。一旦路徑計算完成，回調函式 `_on_planning_done` 會進一步將狀態設為 `EXECUTING`。這造成了 `IDLE` 狀態的「洩漏」，導致任務分配器無法指派新任務。

## Goals / Non-Goals

**Goals:**
- 確保只有處於活動狀態（正在運行或執行任務）的 AGV 在環境變動時觸發重新規劃。
- 防止 `IDLE` 狀態的 AGV 進入規劃與執行流程。

**Non-Goals:**
- 不修改 A* 規劃器或控制器的核心邏輯。
- 不改變 `multiplier` 或物理步長。

## Decisions

### 1. 指令層級的選擇性觸發 (main.py)
在 `backend/main.py` 中處理 `add_obstacle`, `update_obstacle`, `clear_obstacles`, `remove_obstacle` 指令時，遍歷 AGV 時增加狀態檢查：
```python
if t in ["add_obstacle", "update_obstacle", "clear_obstacles", "remove_obstacle"]:
    for a in world.agvs.values():
        if a.is_running: # 僅針對正在運行的 AGV 觸發重新規劃
            a.replan_needed = True
```

### 2. 更新循環層級的狀態守衛 (agv.py)
在 `backend/agv.py` 的 `update` 方法中，對於 `replan_needed` 的處理增加 `is_running` 的判斷：
```python
if self.replan_needed and self.is_running and not self.is_planning:
    all_obs = world.obstacles + world.get_dynamic_obstacles(exclude_agv_id=self.id)
    self._async_replan(all_obs, world.static_costmap, world)
```
這確保了即使 `replan_needed` 被意外設置，`IDLE` 的車輛也不會啟動異步規劃任務。

## Risks / Trade-offs

- **[Risk] 新增障礙物與路徑衝突**：如果 AGV 剛好在 `IDLE` 狀態下，環境在其位置新增了障礙物，它不會立即反應。
  - **Mitigation**: 這被視為正常行為，因為 `IDLE` 車輛本就不應在此時運動。當新任務指派時，它會基於最新環境進行初始規劃。
- **[Trade-off] 代碼複雜度微增**：增加了狀態檢查。
  - **Result**: 極微小的改動換取系統狀態的一致性，利大於弊。
