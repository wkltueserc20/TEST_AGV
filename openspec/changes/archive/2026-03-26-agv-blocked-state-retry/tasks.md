## 1. 後端狀態與類別屬性擴充

- [x] 1.1 在 `backend/agv.py` 的 `AGVStatus` Enum 中新增 `BLOCKED` 與 `ERROR` 狀態。
- [x] 1.2 在 `AGV.__init__` 方法中新增 `self.retry_count = 0`。

## 2. 規劃重試機制實作

- [x] 2.1 修改 `AGV._on_planning_done`，在路徑規劃成功時重置 `retry_count = 0`。
- [x] 2.2 修改 `AGV._on_planning_done` 的規劃失敗邏輯：
    - 當 `retry_count < 3` 時，狀態設為 `BLOCKED`，`retry_count += 1`，並設置 `wait_start_time`。
    - 當 `retry_count >= 3` 時，狀態設為 `ERROR`。
- [x] 2.3 修改 `AGV.update` 方法，處理 `BLOCKED` 狀態下的 2 秒等待邏輯。
- [x] 2.4 在 `BLOCKED` 等待時間結束後，自動觸發 `self.replan_needed = True`。

## 3. 前端 UI 視覺化更新

- [x] 3.1 修改 `frontend/src/SimulatorCanvas.tsx` 的 `statusEmojis` 字典，加入 `BLOCKED` 與 `ERROR` 的 Emoji。
- [x] 3.2 更新 `ledColor` 邏輯，確保 `ERROR` 顯示為紅色，`BLOCKED` 與 `PLANNING` 顏色一致。

## 4. 驗證與測試

- [x] 4.1 模擬路徑規劃失敗（如放置障礙物堵住路徑），觀察是否進入 `BLOCKED` 並重試。
- [x] 4.2 驗證連續 3 次重試失敗後，AGV 是否正確轉向 `ERROR` 狀態。
- [x] 4.3 驗證規劃成功後，`retry_count` 是否正確歸零。
