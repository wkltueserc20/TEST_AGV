## 1. 後端指令處理邏輯優化

- [x] 1.1 修改 `backend/main.py` 中處理環境變動指令（`add_obstacle`, `update_obstacle`, `clear_obstacles`, `remove_obstacle`）的代碼塊。
- [x] 1.2 在遍歷 `world.agvs.values()` 時，增加 `if a.is_running:` 判斷，僅對運行中的 AGV 設置 `replan_needed = True`。

## 2. AGV 狀態機保護實作

- [x] 2.1 修改 `backend/agv.py` 中的 `update` 方法。
- [x] 2.2 找到處理 `replan_needed` 的邏輯區塊，將 `if self.replan_needed and not self.is_planning:` 修改為 `if self.replan_needed and self.is_running and not self.is_planning:`。

## 3. 驗證

- [x] 3.1 啟動模擬器，確保有多台 IDLE 的 AGV。
- [x] 3.2 隨機新增一個圓形或方形障礙物。
- [x] 3.3 觀察 IDLE 的 AGV 是否保持 IDLE 狀態（不應出現 PLANNING 或 EXECUTING 提示）。
- [x] 3.4 確保指派新任務給這些 IDLE 的 AGV 時，它們能正常啟動規劃並執行。
