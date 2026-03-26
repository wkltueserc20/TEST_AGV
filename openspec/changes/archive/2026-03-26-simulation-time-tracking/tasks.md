## 1. 後端數據模型與積分實作

- [ ] 1.1 在 `backend/agv.py` 的 `AGV` 類別中新增 `current_travel_time` 與 `last_travel_time` 屬性。
- [ ] 1.2 更新 `AGV.to_dict()` 方法，包含這兩個新屬性。
- [ ] 1.3 在 `AGV.update(dt, world)` 方法中，實作當 `is_running` 時累加 `current_travel_time += dt` 的邏輯。
- [ ] 1.4 在 `AGV` 狀態切換處（例如抵達目標或被強制設為 IDLE），實作結算邏輯：`last_travel_time = current_travel_time; current_travel_time = 0`。

## 2. 任務與歷史數據追蹤

- [ ] 2.1 在 `backend/world.py` 的 `add_task` 方法中，為任務對象初始化 `execution_time: 0`。
- [ ] 2.2 在 `backend/world.py` 的 `complete_task` 方法中，將執行該任務 AGV 的 `current_travel_time` 紀錄到任務歷史對象中。
- [ ] 2.3 確保 `get_task_queue` 回傳的任務包含從對應 AGV 取得的即時 `execution_time`。

## 3. 前端 UI 顯示與格式化

- [ ] 3.1 在 `frontend/src/App.tsx` 中實作 `formatSimTime(seconds: number)` 格式化工具。
- [ ] 3.2 修改 Fleet Status 渲染邏輯，在 AGV ID 旁顯示 `current_travel_time`（僅在運動中或有值時顯示）。
- [ ] 3.3 在 AGV 卡片下方新增一行，顯示 `Last Run: {formatSimTime(last_travel_time)}`。
- [ ] 3.4 更新任務隊列（Task Queue）與歷史（Task History）列表，加入執行時間顯示。
