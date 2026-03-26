## ADDED Requirements

### Requirement: 全域速度限制指令
後端系統 SHALL 提供一個指令 `set_all_speeds`，用於同時更新所有已註冊 AGV 的最大轉速上限。

#### Scenario: 成功更新所有 AGV 速度
- **WHEN** 系統收到 `{ "type": "set_all_speeds", "data": 1500 }` 指令
- **THEN** 系統中所有 AGV 的 `max_rpm` SHALL 立即變更為 1500
- **AND** 變更後的數據 SHALL 被寫入 `agvs.json`

### Requirement: 全域速度控制介面
前端系統 SHALL 在側邊欄提供一個永久顯示的滑桿，用於發送全域速度限制指令。

#### Scenario: 操作滑桿發送指令
- **WHEN** 使用者拖動全域速度限制滑桿至 2000
- **THEN** 前端 SHALL 透過 WebSocket 發送 `set_all_speeds` 指令，並帶入數值 2000
- **AND** 介面上的標籤 SHALL 即時顯示當前設定值
