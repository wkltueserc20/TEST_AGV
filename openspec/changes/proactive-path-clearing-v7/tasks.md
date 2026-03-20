## 1. Backend Infrastructure

- [x] 1.1 Add `path_occupancy` registry to `World` class in `world.py`.
- [x] 1.2 Implement `update_path_occupancy` and `clear_path_occupancy` methods in `World`.

## 2. AGV Logic Refactor

- [x] 2.1 Simplify `AGVStatus` enum and remove legacy reactive states (`WAIT_AGV`, `WAIT_OBSTACLE`).
- [x] 2.2 Implement `update_occupancy_projection` in `AGV.update` for moving vehicles.
- [x] 2.3 Implement `check_proactive_evasion` for `IDLE` vehicles to detect incoming paths.
- [x] 2.4 Rewrite `trigger_evasion` to use "Backwards-First" strategy and check for unoccupied Havens.
- [x] 2.5 Integrate the new logic into the 50Hz control loop and 100Hz physics loop.
- [x] 2.6 Remove all legacy `culprit_id` and priority arbitration code.

## 3. Telemetry & Visualization

- [x] 3.1 Update `get_snapshot` in `main.py` to broadcast `path_occupancy`.
- [x] 3.2 Update `useSimulation.ts` and `SimulatorCanvas.tsx` to visualize active repulsion zones.
- [x] 3.3 Update frontend status labels to match the simplified state machine.
