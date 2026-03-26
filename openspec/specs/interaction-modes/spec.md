## ADDED Requirements

### Requirement: 互動模式權限矩陣
系統 SHALL 定義並強制執行 ToolMode 權限矩陣，以控制畫布上的滑鼠動作（單擊、雙擊、右擊）。

#### Scenario: 選擇模式唯讀
- **WHEN** 當前模式為 `SELECT` 且使用者點擊物件
- **THEN** 系統 SHALL 選取該物件並在 Sidebar 顯示參數，但禁止任何修改動作（Input 為 disabled）

#### Scenario: 單動模式設定目標
- **WHEN** 當前模式為 `SINGLE_ACTION` 且使用者在畫布上按右鍵
- **THEN** 系統 SHALL 向選中的 AGV 發送 `set_target` 指令

#### Scenario: 方形/圓形模式管理障礙物
- **WHEN** 當前模式為 `BUILD_SQ` 或 `BUILD_CIR` 且使用者在空白處點擊
- **THEN** 系統 SHALL 新增對應類型的障礙物

#### Scenario: 設備模式管理設備與 AGV
- **WHEN** 當前模式為 `BUILD_STAR`
- **THEN** 系統 SHALL 允許新增設備，且 Sidebar 的「+ DEPLOY NEW AGV」按鈕應為可用狀態

#### Scenario: 自動模式右鍵取消
- **WHEN** 當前模式為 `AUTO` 且使用者按右鍵
- **THEN** 系統 SHALL 重置當前任務的起點選取狀態（setAutoTaskSource(null)）
