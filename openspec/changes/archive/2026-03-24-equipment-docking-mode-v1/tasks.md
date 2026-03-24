# Tasks: Equipment Docking Mode

## Phase 1: Backend Implementation
- [x] Add `equipment` obstacle type to `world.py`.
- [x] Implement high-cost logic for `equipment` in `_compute_costmap_task`.
- [x] Modify `update_obstacle` in `world.py` to support renaming an ID (handling `old_id` vs `new_id`).
- [x] Update `obstacles.json` handling to ensure semantic IDs are saved/loaded properly.

## Phase 2: Frontend Rendering & Logic
- [x] Add `BUILD_STAR` to `ToolMode` type in `App.tsx`.
- [x] Create `drawStar` function in `SimulatorCanvas.tsx` (using 2000mm scale).
- [x] Implement equipment rendering in `SimulatorCanvas.tsx` with **status colors** (Yellow/Green/Red).
- [x] Update `handleCanvasClick` in `App.tsx` to add nodes with default `status: 'running'`.
- [x] Update `handleCanvasDoubleClick` in `App.tsx` to support deleting equipment.

## Phase 3: UI & Renaming Feature
- [x] Add "EQUIPMENT" tool button in `App.tsx` toolbar.
- [x] Add editable ID field in Sidebar Inspector when an equipment is selected.
- [x] Implement ID renaming command (`update_obstacle` with `new_id`).
- [x] Add basic ID validation (prevent duplicates).

## Phase 4: Testing & Verification
- [x] Verify star-shaped equipment appears correctly on map.
- [x] Test AGV path planning around and *to* an equipment.
- [x] Verify ID renaming persists after reloading the page.
- [x] Confirm obstacles and equipment are correctly saved to `obstacles.json`.
