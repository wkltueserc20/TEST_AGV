# Implementation Tasks

## 階段 1：後端資料模型升級
- [ ] 在 `AGV.__init__` 中將 `yielding_to_id` 改為 `yielding_to_ids = set()`。
- [ ] 在 `AGV` 類別中新增 `last_yield_check_time = 0.0` 屬性。

## 階段 2：交管與清單收集邏輯
- [ ] 修改 `check_proactive_evasion`：實作掃描所有其他 AGV 並收集 `yielding_to_ids` 的功能。
- [ ] 修改 `_async_replan`：將 `yielding_to_ids` 內的所有路徑合併為 `threat_paths` 傳遞給 `planner`。

## 階段 3：10秒檢查頻率與2秒恢復
- [ ] 在 `AGV.update` 的 `WAITING` 邏輯中實作 10 秒一次的清單清理檢查。
- [ ] 將原本 15 秒的恢復冷卻時間修正為 2 秒。
- [ ] 確保當清單清空後，正確觸發 `_async_replan` 並恢復 `original_target`。

## 階段 4：測試與驗證
- [ ] 建立 `backend/test_three_agvs.py`：配置三台車正面或 T 字路口相遇的場景。
- [ ] 驗證其中一台車是否能正確讓路給另外兩台，並在所有車離開後順利恢復。
