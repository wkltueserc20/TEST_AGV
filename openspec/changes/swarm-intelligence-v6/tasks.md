# Tasks: Swarm Intelligence Implementation

## Phase 1: Controller & Backend Protocol
- [x] Refactor `AGVController.is_pose_safe` to return culprit ID.
- [x] Refactor `AGVController.compute_command` to return culprit ID.
- [x] Update `AGV.update` to capture `culprit_id` and update status machine.

## Phase 2: Escape & Intersection Logic
- [x] Implement BFS-based `find_nearest_intersection` in `AStarPlanner`.
- [x] Implement `trigger_yielding` with intersection-aware escape in `AGV` class.
- [x] Add `RELOCATING` logic for cases where target is occupied.

## Phase 3: Dynamic Priority & Social UI
- [x] Implement priority scoring logic in `AGV`.
- [x] Add `social_links` to telemetry broadcaster in `main.py`.
- [x] Update `SimulatorCanvas.tsx` to render relationship lines and Haven markers.
- [x] Update `App.tsx` with socialized status labels.
