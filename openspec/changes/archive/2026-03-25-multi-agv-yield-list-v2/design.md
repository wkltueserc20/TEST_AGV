# Design: Multi-AGV Yield List & Multiprocessing Architecture

## 1. 架構重構：多進程路徑規劃 (Multiprocessing)
為了解決 Python GIL (Global Interpreter Lock) 導致的 A* 規劃期間物理引擎卡頓問題，系統升級為多進程架構：
- **World 類別**：初始化 `ProcessPoolExecutor`，建立獨立的進程池處理耗時的搜尋任務。
- **純數據接口**：`planner.py` 被重構為純函數接口，不依賴於主進程的 `World` 物件，確保數據可序列化 (Picklable)。
- **非同步回呼**：AGV 提交規劃任務後不阻塞，透過 `_on_planning_done` 回呼函數接收結果並更新狀態。

## 2. 交管邏輯：讓路清單 (Yield List)
將單一讓路對象擴展為集合管理，支援同時避讓多台車輛：
- `AGV.yielding_to_ids`: 使用 `set[str]` 儲存所有當前威脅車輛 ID。
- **偵測範圍**：掃描前方 100 個路徑點，每 5 點採樣一次，並配合 Bounding Box 預判以極大化運算效能。
- **恢復機制**：10 秒低頻檢查清單，清空後 2 秒快速恢復原始任務。

## 3. 效能優化與穩定性
- **稀疏採樣 (Sparse Sampling)**：路徑比對與威脅預處理皆採用採樣技術，運算開銷降低 90% 以上。
- **威脅網格預計算 (Threat Map)**：在 A* 開始前預將所有敵車路徑轉換為網格集合，搜尋複雜度從 O(N*M) 降至 O(1)。
- **GIL 主動釋放**：在 A* 密集迴圈中使用 `time.sleep(0)`，確保 WebSocket 與通訊線程不被餓死。
- **設備安全啟動**：
    - 起點 2.5 米內暫不觸發避讓。
    - 規劃時若在設備內部，則降低動態障礙物權重（0.1x），確保能順利「出門」。
- **座標容錯判定**：裝卸料判定改用物理座標比對，並放寬至 500mm 容錯，解決避讓後座標微偏導致卡在 WAITING 的問題。

## 4. 狀態機變更
- `THINKING`: 正在向進程池提交規劃任務或尋找避讓點。
- `YIELDING`: 正在前往多進程算出的避讓路徑點。
- `WAITING`: 到達避讓點，或在無任務/判定不明時的緩衝狀態。
