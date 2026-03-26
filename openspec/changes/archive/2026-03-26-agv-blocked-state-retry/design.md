## Context

當前 AGV 系統在遇到規劃失敗時，缺乏一個暫時性的「阻塞 (Blocked)」狀態，且沒有自動重試邏輯。這導致系統在遇到瞬態障礙（如其他車輛經過）時容易進入 `STUCK` 狀態，需手動重置。

## Goals / Non-Goals

**Goals:**
- 在 `AGVStatus` 中引入 `BLOCKED` 與 `ERROR` 狀態。
- 實作「重試 3 次，每次間隔 2 秒」的自動規劃恢復機制。
- 在前端 UI 同步顯示這些新狀態。

**Non-Goals:**
- 不改變 A* 搜尋演算法本身。
- 不實作更複雜的避障策略（如繞道演算法的修改）。

## Decisions

### 1. 狀態機擴充
在 `backend/agv.py` 的 `AGVStatus` Enum 中新增：
- `BLOCKED`: 表示暫時性的規劃失敗。
- `ERROR`: 表示重試多次後的永久性失敗。

### 2. 重試邏輯管理
在 `AGV` 類別中新增 `self.retry_count` 屬性。
- 修改 `_on_planning_done` 回調：
    - 規劃成功：`self.retry_count = 0`。
    - 規劃失敗：`self.retry_count += 1`；若仍在範圍內則狀態設為 `BLOCKED`，否則設為 `ERROR`。
- 修改 `update` 方法：
    - 若狀態為 `BLOCKED` 且 `time.time() - self.wait_start_time > 2.0`，則設置 `self.replan_needed = True`。

### 3. 前端 UI 回饋
修改 `frontend/src/SimulatorCanvas.tsx`：
- 在 `statusEmojis` 字典中新增 `BLOCKED: '🚧'` 與 `ERROR: '❌'`。
- 更新 `ledColor` 邏輯，使 `ERROR` 顯示為紅色。

## Risks / Trade-offs

- **[Risk] 重試次數過多導致死鎖** ➔ **Mitigation**: 嚴格限制重試次數為 3 次，之後進入 `ERROR` 狀態，由系統核心或操作員介入。
- **[Trade-off] 延遲回饋** ➔ 使用 2 秒的重試間隔是為了給環境留出變化空間，這會讓反應顯得稍慢，但能提高自動恢復率。
