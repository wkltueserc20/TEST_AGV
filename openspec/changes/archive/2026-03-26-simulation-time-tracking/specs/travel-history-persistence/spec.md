## ADDED Requirements

### Requirement: 保存上一次行走紀錄
系統 SHALL 在 AGV 數據模型中保存上一次完整行走任務的總耗時。

#### Scenario: 查詢 AGV 歷史效能
- **WHEN** 呼叫 `to_dict()` 獲取 AGV 快照
- **THEN** 回傳的數據 SHALL 包含 `last_travel_time` 欄位
