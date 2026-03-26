## ADDED Requirements

### Requirement: 前端樂觀更新機制
系統 SHALL 實作樂觀更新機制，使物件在發送 WebSocket 指令後能即時於畫面上呈現，不需等待後端 telemetry 回傳。

#### Scenario: 樂觀新增障礙物
- **WHEN** 使用者點擊畫布以新增障礙物
- **THEN** 系統 SHALL 立即在 `pendingObstacles` 中建立一個帶有臨時 ID 的物件並在畫布上渲染，隨後再發送指令

#### Scenario: 同步後端確認
- **WHEN** 收到 `telemetry` 且包含與 `pendingObstacles` 座標一致的新物件
- **THEN** 系統 SHALL 從 `pendingObstacles` 移除該臨時物件，並改以真實物件渲染

#### Scenario: 樂觀刪除障礙物
- **WHEN** 使用者雙擊物件以進行刪除
- **THEN** 系統 SHALL 立即將該 ID 加入 `pendingDeletions` 集合並停止渲染該物件，隨後發送指令
