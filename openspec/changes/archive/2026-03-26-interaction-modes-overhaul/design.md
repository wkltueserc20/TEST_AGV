## Context
目前的系統將所有的互動邏輯分散在 `App.tsx` 的 `handleCanvasClick` 與 `SimulatorCanvas.tsx` 的事件轉發中。權限檢查不夠集中，且新增物件時必須等待 WebSocket 往返，導致 UI 反應遲鈍。

## Goals / Non-Goals

**Goals:**
- 將 `ToolMode` 擴展為包含單動模式（SINGLE_ACTION）。
- 實作集中式的「權限矩陣」，控制不同模式下的畫布行為（點擊、雙擊、右鍵）。
- 引入「樂觀更新」機制，使新增與刪除障礙物在本地即時反映。
- 確保 Sidebar 的輸入欄位（Input）在選擇模式下為唯讀。

**Non-Goals:**
- 不涉及後端 `obstacles.json` 的儲存邏輯優化（僅前端優化）。
- 不改變現有的任務調度算法。

## Decisions

### 1. 互動模式矩陣 (Interaction Matrix)
在 `App.tsx` 中定義一個對象，集中管理權限。例如：
```typescript
const MODE_PERMISSIONS = {
  SELECT: { canAdd: false, canDelete: false, canEdit: false, rightClick: 'NONE' },
  SINGLE_ACTION: { canAdd: false, canDelete: false, canEdit: false, rightClick: 'SET_TARGET' },
  BUILD_SQ: { canAdd: 'OBSTACLE', canDelete: true, canEdit: true, rightClick: 'NONE' },
  // ... 其他模式
};
```
這比在 `handleCanvasClick` 中寫大量 `if-else` 更易維護。

### 2. 樂觀更新狀態管理 (Optimistic State)
在 `App.tsx` 加入 `pendingObstacles` 狀態：
- **新增時**：前端生成一個臨時 ID（以 `pending-` 開頭），立刻加入本地列表並發送 WebSocket。
- **收到 Telemetry 時**：比對 ID。如果 `telemetry.obstacles` 中出現了與本地坐標吻合的物件，則移除 `pending` 狀態。
- **刪除時**：維護一個 `pendingDeletions` ID 集合，渲染時過濾掉這些 ID。

### 3. 自動模式 (AUTO) 的右鍵行為
當 `activeTool === 'AUTO'` 時，右鍵點擊將呼叫 `setAutoTaskSource(null)`，重置任務選取狀態。這對使用者來說是一個快速修正選錯起點的操作。

### 4. 側邊欄 (Sidebar) 的唯讀控制
根據 `activeTool` 控制所有設定面板的 `disabled` 或 `readOnly` 屬性。在 `SELECT` 模式下，使用者可以點選 AGV 或設備查看參數，但無法修改 ID、座標或角度。

## Risks / Trade-offs

- **[Risk] ID 衝突**：樂觀更新生成的臨時 ID 可能與後端生成的 ID 不一致。
  - **Mitigation**: 樂觀更新在匹配回傳資料時，應優先比對「座標與類型」，而不僅是 ID。一旦後端正式 ID 回傳，立即更新本地參照。
- **[Risk] 指令失敗**：如果後端新增失敗（例如網路斷線），樂觀更新會讓物件短暫出現後消失。
  - **Mitigation**: 這被認為是可接受的權衡，因為它能提供極佳的互動反應。

## Open Questions
- 是否需要在「選擇 (SELECT)」模式下也顯示右鍵選單，還是完全禁用右鍵？（目前規劃是完全禁用以符合「純查看」的直覺）。
