## ADDED Requirements

### Requirement: 有條件的重新規劃觸發
當環境障礙物發生變動時，系統 SHALL 僅針對處於運行狀態（`is_running == True`）的 AGV 觸發重新規劃請求。

#### Scenario: IDLE 車輛忽略環境變動
- **WHEN** 系統收到 `add_obstacle` 指令
- **AND** 車輛 `AGV-001` 的 `is_running` 為 `False`
- **THEN** 該車輛的 `replan_needed` SHALL 保持為 `False`

#### Scenario: 運行中車輛響應環境變動
- **WHEN** 系統收到 `update_obstacle` 指令
- **AND** 車輛 `AGV-002` 的 `is_running` 為 `True`
- **THEN** 該車輛的 `replan_needed` SHALL 被設為 `True`

### Requirement: 狀態機保護守衛
在 AGV 更新循環中，系統 SHALL 強制檢查車輛是否真的需要且能夠執行規劃任務。

#### Scenario: 防止 IDLE 車輛進入 PLANNING 狀態
- **WHEN** AGV 的 `replan_needed` 為 `True` 但 `is_running` 為 `False`
- **THEN** 系統 SHALL 不呼叫 `_async_replan` 方法
- **AND** 該車輛狀態 SHALL 維持 `IDLE`
