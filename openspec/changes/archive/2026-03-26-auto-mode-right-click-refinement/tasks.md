## 1. 前端邏輯修改

- [x] 1.1 在 `frontend/src/App.tsx` 中，找到 `onCanvasRightClick` 的定義處。
- [x] 1.2 在 `perm === 'CANCEL_TASK'` 的條件分支內，加入 `setSelectedAgvId(null)` 與 `setSelectedObId(null)`。
- [x] 1.3 驗證在 `AUTO` 模式下右鍵點擊畫布時，側邊欄的選中狀態與任務起點均被重置。
