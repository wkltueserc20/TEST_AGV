# Design: Priority-Based Traffic Control

## 1. 狀態機擴展 (State Machine Extension)
在 `backend/agv.py` 中的 `AGVStatus` 擴增以下狀態：
- `WAITING`: 因為被高優先級車輛擋住，或已到達中繼點等待路徑清空。
- `THINKING`: 發現衝突，正在進行優先級計算與尋找避讓的中繼安全點。
- `YIELDING`: 正在前往中繼安全點（避讓移動中）。

## 2. 衝突偵測邏輯 (Collision Detection - 100 points)
在 `check_proactive_evasion` 中實作深度預判：
1. 獲取自身的 `global_path[:100]`。
2. 獲取其他 AGV 的 `global_path[:100]`。
3. 如果任意兩點的平方距離 `< 6250000` (2.5m 的平方)，則判定為發生路徑衝突。

## 3. 優先級與仲裁 (Priority & Arbitration)
當偵測到衝突時，進入仲裁邏輯：
```python
def get_priority(self):
    # 數字越小代表優先級越高。沒有任務則優先級最低 (例如 100)
    if not self.current_task: return 100
    return self.current_task.get("priority", 5)
```
- 若 `self.priority > other.priority` (我方優先級較低)：我方執行閃避。
- 若 `self.priority < other.priority` (我方優先級較高)：我方繼續執行任務 (讓對方閃避)。
- 若 `self.priority == other.priority`：
  - 若 `self.id < other.id`：我方執行閃避（ID小的讓行）。
  - 若 `self.id > other.id`：我方繼續執行任務。

## 4. 中繼點搜尋與閃避 (Yielding Behavior)
被選定需閃避的 AGV 將執行以下動作：
1. 狀態切換為 `THINKING`。
2. 呼叫 `planner.find_nearest_safe_spot`，並將**對方的高優先級路徑**作為 `threat_paths` 傳入，確保找到的點不在對方未來的路徑上。
3. 找到中繼安全點後，暫存原來的目標 `original_target`，將當前目標設為安全點。
4. 狀態切換為 `YIELDING`，前往該點。
5. 到達中繼點後，狀態切換為 `WAITING`。

## 5. 任務恢復機制 (Task Resumption)
在 `WAITING` 狀態的更新迴圈中：
- 檢查 `world.path_occupancy[other_id]` 是否還與**我的原始目標路徑**發生重疊。
- 如果不再重疊（代表對方已經通過或改變路徑）：
  - 狀態切換回 `PLANNING`。
  - `self.target` 恢復為 `original_target`。
  - 觸發 `_async_replan` 重新規劃路徑，繼續原任務。
