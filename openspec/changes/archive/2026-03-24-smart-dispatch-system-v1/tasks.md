# Tasks: Smart Logistics Dispatch System

## Phase 1: Data Model & Basic UI
- [x] Add `has_goods` to equipment JSON and `AGV` class.
- [x] Add `AUTO` to `ToolMode` in `App.tsx`.
- [x] Implement cargo rendering (Orange Cube) in `SimulatorCanvas.tsx`.
- [x] Add `Has Goods` toggle in Equipment Inspector.

## Phase 2: Dispatcher & Queue Logic
- [x] Implement `task_queue` and `task_history` in `backend/world.py`.
- [x] Implement the `dispatch_task` logic in `backend/main.py`.
- [x] Add proximity-based auto-assignment logic for `IDLE` AGVs.
- [x] Display the current `Waiting List` and `Mission History` in the sidebar.

## Phase 3: AGV Task Execution (The State Machine)
- [x] Implement 5-second timer for `LOADING` and `UNLOADING` in `agv.py`.
- [x] Implement cargo transfer logic (Equipment <-> AGV).
- [x] Ensure AGV automatically transitions from `PICKING` -> `LOADING` -> `DELIVERING` -> `UNLOADING` -> `IDLE`.

## Phase 4: Interaction, Locking & Priority
- [x] Implement the A -> B click sequence in `App.tsx`.
- [x] Add mission-based priority: Mission vehicles have the right of way and do not evade.
- [x] Implement early proactive evasion for IDLE vehicles based on global path projection.
- [x] Implement resource locking to prevent double-booking of stations.
- [x] Add direct AGV assignment (Station ➔ AGV) for specific pick/drop tasks.
