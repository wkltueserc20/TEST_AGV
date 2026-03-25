# Implementation Tasks

## 階段 1：後端狀態機與優先級基礎
- [x] 在 `backend/agv.py` 的 `AGVStatus` 中新增 `WAITING`, `THINKING`, `YIELDING` 狀態。
- [x] 在 `AGV` 類別中新增 `get_priority()` 方法，依據 `current_task` 回傳優先級。
- [x] 擴充 `AGV` 屬性，新增 `original_target` 與 `yielding_to_id` 來記憶被中斷的任務與讓行的對象。

## 階段 2：交管與仲裁邏輯
- [x] 改寫 `check_proactive_evasion` 函式。
- [x] 將路徑掃描範圍從目前的簡單點位擴展為 `path[:100]` 與對方的 `path[:100]` 交叉比對平方距離。
- [x] 實作優先級比較 (`self.priority` vs `other.priority`) 與 ID 仲裁邏輯 (`self.id < other.id`)。

## 階段 3：避讓與恢復機制
- [x] 實作 `YIELDING` 行為：呼叫 `find_nearest_safe_spot` 尋找中繼點，將高優先車輛的路徑列為 `threat_paths`。
- [x] 在 `AGV.update` 的迴圈中加入恢復邏輯：當狀態為 `WAITING` (或 `YIELDING`) 時，監測 `world.path_occupancy`，確認與 `yielding_to_id` 的路徑是否已解開衝突。
- [x] 路徑清空後，還原 `self.target` 並觸發 `_async_replan`，狀態切換回 `PLANNING`。

## 階段 4：前端顯示與整合
- [x] 更新 `frontend/src/SimulatorCanvas.tsx` 中繪製 AGV 的狀態文字與顏色對應，支援 `WAITING` (例如顯示 ⏸️), `THINKING` (🧠), `YIELDING` (🛡️)。
- [x] 建立或修改測試腳本 (例如 `test_priority.py`)，配置兩台執行任務的 AGV 正面相遇的場景，驗證交管邏輯。
