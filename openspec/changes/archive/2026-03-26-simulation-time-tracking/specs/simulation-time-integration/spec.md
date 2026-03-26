## ADDED Requirements

### Requirement: 模擬時間積分邏輯
系統 SHALL 在物理引擎更新循環中，根據實時時間間隔（real_dt）與模擬倍率（multiplier）累算模擬時間。

#### Scenario: 加速模擬下的時間累加
- **WHEN** 模擬倍率設為 10x 且現實時間經過 1 秒
- **THEN** AGV 的 `current_travel_time` SHALL 增加 10 秒

### Requirement: 自動結算任務耗時
當 AGV 完成任務並切換回 IDLE 狀態時，系統 SHALL 將當前耗時結算至歷史耗時。

#### Scenario: 任務完成後的耗時轉移
- **WHEN** AGV 完成最後一個路徑點並進入 IDLE 狀態
- **THEN** AGV 的 `last_travel_time` SHALL 更新為本次任務的總耗時，且 `current_travel_time` SHALL 歸零
