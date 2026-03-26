## ADDED Requirements

### Requirement: AGV Blocked State and Retry Mechanism
當 AGV 在進行路徑規劃 (Planning) 或主動避讓規劃 (Thinking) 失敗時，系統 SHALL 進入 `BLOCKED` 狀態，並啟動自動重試機制。

#### Scenario: First planning failure triggers BLOCKED state
- **WHEN** `planner.get_path` 返回空路徑（規劃失敗）且 `retry_count` 為 0
- **THEN** AGV 狀態 MUST 設為 `BLOCKED`，`retry_count` 增加 1，並記錄 `wait_start_time`

#### Scenario: Automatic retry after wait period
- **WHEN** AGV 處於 `BLOCKED` 狀態且距離 `wait_start_time` 已超過 2 秒
- **THEN** 系統 SHALL 將 `replan_needed` 設為 `True` 並重新嘗試規劃

#### Scenario: Transition to ERROR after maximum retries
- **WHEN** `retry_count` 超過 3 次且路徑規劃依然失敗
- **THEN** AGV 狀態 MUST 設為 `ERROR`，停止所有動作，並清空 `retry_count`

#### Scenario: Successful planning resets retry count
- **WHEN** AGV 成功取得有效路徑
- **THEN** 系統 SHALL 將 `retry_count` 重設為 0

### Requirement: Enhanced UI Status Visualization
前端介面 SHALL 明確顯示 AGV 的 `BLOCKED` 與 `ERROR` 狀態，以便操作員識別。

#### Scenario: Display blocked state in canvas
- **WHEN** AGV 狀態為 `BLOCKED`
- **THEN** 畫布上對應 AGV 的狀態標籤 MUST 顯示為 "🚧 BLOCKED"，且 LED 燈號應顯示為黃色 (或是與 PLANNING 相同的顏色)

#### Scenario: Display error state in canvas
- **WHEN** AGV 狀態為 `ERROR`
- **THEN** 畫布上對應 AGV 的狀態標籤 MUST 顯示為 "❌ ERROR"，且 LED 燈號 MUST 顯示為紅色
