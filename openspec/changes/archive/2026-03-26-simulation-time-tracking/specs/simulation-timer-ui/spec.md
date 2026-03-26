## ADDED Requirements

### Requirement: 模擬時間格式化
前端系統 SHALL 提供一個工具函式，將秒數（seconds）轉換為「xxx分xx秒」格式。

#### Scenario: 時間格式化範例
- **WHEN** 輸入值為 125 秒
- **THEN** 格式化結果 SHALL 為「2分05秒」

### Requirement: 即時時間顯示
系統 SHALL 在 Fleet Status 卡片與 Task Queue 列表中，針對正在運動的 AGV 顯示即時模擬計時。

#### Scenario: 運動中的計時呈現
- **WHEN** AGV 處於 EXECUTING 狀態且 `current_travel_time` 為 10.5
- **THEN** UI 應在 ID 旁顯示「0分10秒」
