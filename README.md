# 多機差速 AGV 高精模擬器 (V5.1 Pro)

這是一個工業級的高精度多機 AGV (Automated Guided Vehicle) 模擬系統。採用 **Python FastAPI** 作為運算後端，配合 **React (TypeScript)** 作為可視化前端，實作了結合 **物理勢場 A*** 與 **動態 DWA** 的混合導航架構。

![AGV Simulation](https://img.shields.io/badge/Version-5.6-green)
![Architecture](https://img.shields.io/badge/Architecture-Async--Queue-orange)
![Performance](https://img.shields.io/badge/Performance-Ultra--Responsive-blue)

## 🚀 核心特色

### 1. V5.6 非同步響應引擎 (Async Engine)
- **零阻塞操作**：障礙物刪除、清除與 F5 重新整理均實現了非同步處理。重型運算在地圖背景執行緒完成，UI 隨時保持即時響應。
- **雙擊快速互動**：新增「雙擊刪除障礙物」功能，大幅提升場景佈置效率。

### 2. 極致效能與視覺化
- **100x 規劃加速**：採用預處理代價地圖（Static Costmap），複雜路徑瞬間生成。
- **A* 搜尋可見化**：動態展示搜尋過程，支援逐格流水重播，是演算法除錯的最佳利器。

### 2. V5.0+ 多機協同與避障 (Multi-AGV Coordination)
- **全場域互感應**：AGV 之間能實時感知彼此位置，並自動將其他車輛視為動態圓形障礙物。
- **物理勢場 A***：路徑會根據兩側牆壁壓力自動尋找力量平衡的「中心中線」，並透過「雙重移動平均」生成平滑的圓弧轉彎軌跡。
- **外擺補償 (Swing-out)**：轉彎時自動補償內外輪差，確保 1m 車體在 2m 通道中完美過彎。

### 3. 高精度物理模擬 (Industrial-Grade Physics)
- **100Hz 子步進積分**：內部物理週期達 10ms，徹底消除高倍速模擬下的積分漂移。
- **嚴格 RPM 限制**：鎖定 3000 RPM (600mm/s) 物理極限，具備單輪超速保護與動態加速度限制。
- **動態倍率**：支援 1x ~ 15x 模擬加速，方便快速驗證不同場景下的演算法表現。

## ⚙️ 快速啟動 (Windows)

專案內建了一鍵啟動腳本，會自動初始化環境並啟動服務：
```powershell
.\start.ps1
```

## 🎮 操作說明

- **左鍵點擊**：點擊空白處「新增」障礙物（吸附於網格）；點擊障礙物「選取」編輯。
- **右鍵點擊**：設定選中 AGV 的 **目標 B 點**（自動吸附於格線交點）。
- **側邊欄管理**：
  - **模擬速度**：切換 1x ~ 15x 運行速度。
  - **Fleet Management**：管理多台 AGV 狀態。
  - **即時遙測**：觀察座標、絕對角度與左右輪即時 RPM。
- **自動存檔**：場景佈置會自動序列化至 `backend/obstacles.json`。

## 📄 技術架構

```text
├── backend/
│   ├── world.py        # 世界引擎：管理邊界、障礙物與多機同步
│   ├── agv.py          # AGV 實體：自治導航與非同步規劃邏輯
│   ├── planner.py      # 高解析度勢場 A* 規劃器
│   ├── controller.py   # 具備外擺補償與安全護盾的局部控制器
│   ├── main.py         # FastAPI 伺服器與倍率調度
│   └── obstacles.json  # 場景存檔
├── frontend/
│   ├── src/
│   │   ├── SimulatorCanvas.tsx # 高效能 60FPS 渲染引擎
│   │   └── App.tsx             # 專注編輯模式 UI
└── start.ps1           # 自動化啟動腳本
```
