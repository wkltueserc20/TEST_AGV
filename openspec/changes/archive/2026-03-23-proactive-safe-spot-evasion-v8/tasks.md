## 1. Cleanup and Infrastructure

- [x] 1.1 Remove legacy evasion methods from `backend/agv.py`.
- [x] 1.2 Update `AGVStatus` enum (`IDLE`, `PLANNING`, `EXECUTING`, `EVADING`, `STUCK`).
- [x] 1.3 Add `evasion_target` field to `AGV` class and its `to_dict` method.

## 2. Safe-Spot Implementation

- [x] 2.1 Implement `find_nearest_safe_spot` in `backend/planner.py` using BFS (25m range).
- [x] 2.2 Add 1000x1000mm footprint validation.
- [x] 2.3 Optimize circular threat zones (2.0m radius).

## 3. AGV Logic Refactor

- [x] 3.1 Implement full-trajectory intent broadcasting.
- [x] 3.2 Implement One-Shot evasion trigger using background threads.
- [x] 3.3 Add Social Braking (Mission AGVs wait for Evaders).

## 4. Visualization & Verification

- [x] 4.1 Broadcast `reserved_havens` in telemetry.
- [x] 4.2 Add `evasion_target` to `AGVData` interface.
- [x] 4.3 Render Haven markers (purple X) on canvas.
- [x] 4.4 Align frontend status labels.
