## 1. 後端實作

- [x] 1.1 在 `backend/main.py` 的指令處理迴圈中新增 `set_all_speeds` 處理分支。
- [x] 1.2 實作遍歷 `world.agvs` 並更新所有 `max_rpm` 的邏輯。
- [x] 1.3 確保更新後呼叫 `world.save_agvs()` 以儲存設定。

## 2. 前端實作

- [x] 2.1 在 `frontend/src/App.tsx` 的 `App` 組件中新增 `globalRpm` state 與初始值 3000。
- [x] 2.2 在左側側邊欄的「System Control」區塊下方新增全域速度限制滑桿 UI。
- [x] 2.3 實作滑桿的 `onChange` 事件，同步更新 `globalRpm` 並發送 `set_all_speeds` 指令。
- [x] 2.4 移除原本位於 `selectedAgv` 區塊中的單機速度限制 UI。

## 3. 驗證

- [x] 3.1 啟動系統，嘗試拖動全域速度滑桿。
- [x] 3.2 驗證所有 AGV 的 `max_rpm` 是否同步變更。
- [x] 3.3 重新啟動後端，確認 `max_rpm` 是否成功持久化。
