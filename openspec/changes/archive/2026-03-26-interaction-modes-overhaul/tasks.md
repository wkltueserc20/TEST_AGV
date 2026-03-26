## 1. 基礎架構與 ToolMode 擴充

- [x] 1.1 在 `App.tsx` 的 `ToolMode` 類型中加入 `SINGLE_ACTION`。
- [x] 1.2 在 `App.tsx` 中定義 `MODE_PERMISSIONS` 權限對象。
- [x] 1.3 在 `App.tsx` 的 Toolbar 渲染處新增「單動模式 (SINGLE_ACTION)」按鈕並配上對應的圖示/文字。

## 2. 畫布事件重構 (Interaction Overhaul)

- [x] 2.1 重構 `handleCanvasClick`：根據 `MODE_PERMISSIONS` 檢查是否有新增障礙物或設備的權限。
- [x] 2.2 重構 `handleCanvasDoubleClick`：根據模式檢查是否有刪除權限。
- [x] 2.3 重構 `onCanvasRightClick`：
    - `SINGLE_ACTION` 模式下：執行 `set_target`。
    - `AUTO` 模式下：執行 `setAutoTaskSource(null)`。
    - 其他模式：不執行任何動作（e.preventDefault() 即可）。

## 3. 樂觀渲染 (Optimistic Rendering)

- [x] 3.1 在 `App.tsx` 加入 `pendingObstacles` 與 `pendingDeletions` 狀態。
- [x] 3.2 在 `handleCanvasClick` 新增物件時，立刻更新 `pendingObstacles`。
- [x] 3.3 在 `handleCanvasDoubleClick` 刪除物件時，立刻更新 `pendingDeletions`。
- [x] 3.4 在收到 `telemetry` 的 `useEffect` 中加入比對與清理邏輯，將後端已確認的物件從 `pending` 中移除。
- [x] 3.5 修改傳給 `SimulatorCanvas` 的 `telemetry` prop（或是對其進行包裝），將 `pendingObstacles` 合併並過濾 `pendingDeletions`。

## 4. UI 限制與優化 (UI Constraints)

- [x] 4.1 在 `App.tsx` 的 Sidebar 中，根據模式權限設定 Input 的 `disabled` 或 `readOnly`。
- [x] 4.2 確保「+ DEPLOY NEW AGV」與「WIPE ALL OBSTACLES」按鈕僅在對應的建築模式下啟用。
- [x] 4.3 更新 `mode-status-bar` 的提示文字，使其更準確地描述新模式的操作。
