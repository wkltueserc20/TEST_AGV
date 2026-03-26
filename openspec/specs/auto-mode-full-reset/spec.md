## ADDED Requirements

### Requirement: AUTO 模式右鍵一鍵重置
系統 SHALL 在 `AUTO` 模式下點擊右鍵時，清空所有與任務選取及物件選取相關的臨時狀態。

#### Scenario: 成功執行一鍵重置
- **WHEN** 當前 `activeTool` 為 `AUTO` 且畫布觸發 `onContextMenu` 事件
- **THEN** 系統 SHALL 呼叫 `setAutoTaskSource(null)`
- **AND** 系統 SHALL 呼叫 `setSelectedAgvId(null)`
- **AND** 系統 SHALL 呼叫 `setSelectedObId(null)`
