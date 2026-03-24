# Tasks: Smart Logistics Dispatch System

## Phase 1: Data Model & Basic UI
- [ ] Add `has_goods` to equipment JSON and `AGV` class.
- [ ] Add `AUTO` to `ToolMode` in `App.tsx`.
- [ ] Implement cargo rendering (Orange Cube) in `SimulatorCanvas.tsx`.
- [ ] Add `Has Goods` toggle in Equipment Inspector.

## Phase 2: Dispatcher & Queue Logic
- [ ] Implement `task_queue` in `backend/world.py`.
- [ ] Implement the `dispatch_task` logic in `backend/main.py` and `world.py`.
- [ ] Add proximity-based auto-assignment logic for `IDLE` AGVs.
- [ ] Display the current `Waiting List` in the sidebar.

## Phase 3: AGV Task Execution (The State Machine)
- [ ] Implement 5-second timer for `LOADING` and `UNLOADING` in `agv.py`.
- [ ] Implement cargo transfer logic (Equipment <-> AGV).
- [ ] Ensure AGV automatically transitions from `PICKING` -> `LOADING` -> `DELIVERING` -> `UNLOADING` -> `IDLE`.

## Phase 4: Integration & AUTO Mode Interaction
- [ ] Implement the A -> B click sequence in `App.tsx`.
- [ ] Add visual feedback for "Source Selected" in AUTO mode.
- [ ] Verify the whole loop: User clicks -> Task Queues -> AGV picks nearest -> Mission completes.
