# Tasks: Precision Docking Angle

## Phase 1: UI & Data Model
- [x] Add `docking_angle` field to equipment default values in `App.tsx`.
- [x] Add Angle numeric input field in Sidebar Inspector for `equipment` type.
- [x] Implement rendering logic for the **Directional Arrow** on stars in `SimulatorCanvas.tsx`.
- [x] Ensure `docking_angle` is saved and loaded from `obstacles.json`.

## Phase 2: Planner Logic (Option A)
- [x] Update `get_path` in `planner.py` to detect equipment targets.
- [x] Implement "Approach Waypoint" calculation logic (1500mm offset).
- [x] Modify path generation to chain `[A* to Approach] + [Center]`.
- [x] Add safety check: if Approach Point is inside an obstacle, fallback to direct A*.

## Phase 3: AGV Logic & Pose Alignment
- [x] Update `AGV.update` in `agv.py` to include heading error in mission completion check.
- [x] Implement final rotation logic to align with `docking_angle` after reaching the center.
- [x] Ensure mission status only switches to `IDLE` after pose is fully aligned.

## Phase 4: Testing & Polish
- [x] Verify AGV approaches equipment from the correct direction.
- [x] Verify visual arrow updates correctly when changing equipment angle.
- [x] Test edge cases (equipment near walls, 0/90/180/270 degree tests).
