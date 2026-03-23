# Design: AGV DWA Simulator

## 1. Physical Model & Kinematics
### 1.1 Differential Drive Model
*   **Wheel Radius (r)**: 假設 $D = 38.2mm \Rightarrow r = 19.1mm$ (以符合 3000RPM = 600mm/s)。
*   **Wheel Base (L)**: 假設 $L = 800mm$ (1m x 1m 車體)。
*   **Speed Calculation**:
    *   $v_L = (RPM_L / 60) * 2\pi * r$
    *   $v_R = (RPM_R / 60) * 2\pi * r$
    *   $v = (v_R + v_L) / 2$ (Linear Velocity)
    *   $\omega = (v_R - v_L) / L$ (Angular Velocity)

### 1.2 Coordinate Mapping
*   **Physical (x, y)**: (0,0) at Bottom-Left.
*   **Canvas (cx, cy)**: (0,0) at Top-Left.
*   **Transformation**:
    *   $cx = x * scale$
    *   $cy = (MapHeight - y) * scale$

## 2. DWA Algorithm Logic
*   **State**: $[x, y, \theta, v, \omega]$
*   **Dynamic Window (DW)**:
    *   $V_{max} = 600 mm/s$
    *   $V_{min} = 0 mm/s$
    *   考慮加速度限制 $\Delta v, \Delta \omega$。
*   **Trajectory Prediction**: 預測未來 2.0 秒的路徑。
*   **Evaluation Function**:
    *   $G(v, \omega) = \sigma (\alpha \cdot heading + \beta \cdot dist + \gamma \cdot velocity)$
    *   $heading$: 指向目標 B 的精確度。
    *   $dist$: 距離最近障礙物的距離（考慮 1m x 1m Footprint）。
    *   $velocity$: 越接近極速分數越高。

## 3. Communication Protocol (WebSockets)
*   **Server -> Client (Telemetry)**:
    ```json
    {
      "type": "telemetry",
      "data": { "x": float, "y": float, "theta": float, "l_rpm": float, "r_rpm": float, "diff": float }
    }
    ```
*   **Client -> Server (Command)**:
    ```json
    { "type": "add_obstacle", "data": { "shape": "circle", "x": 100, "y": 200, "r": 50 } }
    { "type": "remove_obstacle", "id": "uuid" }
    ```

## 4. UI Layout (React)
*   **Left (Sidebar)**: 障礙物列表、Delete 按鈕、實時 RPM 儀表。
*   **Center**: HTML5 Canvas (50m x 50m 縮放顯示)。
*   **Bottom**: 控制按鈕 (Start, Pause, Reset, B點設定)。
