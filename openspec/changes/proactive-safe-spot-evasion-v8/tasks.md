## 1. Cleanup and Infrastructure

- [ ] 1.1 Remove legacy evasion methods from `backend/agv.py` (`check_proactive_evasion`, `trigger_evasion`, `_is_directional_safe`, `_is_haven_safe`).
- [ ] 1.2 Update `AGVStatus` enum to match simplified design (`IDLE`, `PLANNING`, `EXECUTING`, `EVADING`, `STUCK`).
- [ ] 1.3 Add `evasion_target` field to `AGV` class and its `to_dict` method.

## 2. Safe-Spot Implementation

- [ ] 2.1 Implement `find_nearest_safe_spot` in `backend/planner.py` using BFS.
- [ ] 2.2 Add 1000x1000mm footprint validation to the BFS search.
- [ ] 2.3 Optimize the search by pre-calculating threat grids from `world.path_occupancy`.

## 3. AGV Logic Refactor

- [ ] 3.1 Implement `is_conflicted` method in `AGV` to detect path overlaps at 5Hz.
- [ ] 3.2 Implement unified evasion trigger in `AGV.update` using `find_nearest_safe_spot` and standard A* planning.
- [ ] 3.3 Ensure `EVADING` status is maintained until the safe spot is reached or a new conflict arises.

## 4. Visualization & Verification

- [ ] 4.1 Update `get_snapshot` in `backend/main.py` to include `evasion_target` in telemetry.
- [ ] 4.2 Update `frontend/src/useSimulation.ts` to include `evasion_target` in the `AGVData` interface.
- [ ] 4.3 Update `frontend/src/SimulatorCanvas.tsx` to render evasion markers (e.g., purple dashed circle).
- [ ] 4.4 Update frontend status labels to match new `AGVStatus`.
