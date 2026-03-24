# Proposal: Smart Logistics Dispatch System

## Summary
Transform the AGV simulator into a logistics system by introducing cargo states, an AUTO mode for mission creation, a waiting queue, and a proximity-based task dispatcher.

## Goals
- Add `has_goods` property to both equipment and AGVs.
- Implement an **AUTO Mode** for creating "Pick-and-Drop" tasks by selecting two equipment nodes.
- Implement a **Proximity-Based Task Dispatcher**:
  - Assign tasks to the nearest IDLE AGV immediately.
  - If busy, place tasks in a `Waiting List`.
  - When an AGV becomes IDLE, it picks the nearest task from the list.
- Add a **5-second delay** for Loading/Unloading animations and state updates.

## Technical Scope
- **Backend (`world.py`, `agv.py`)**:
  - Extend data models with `has_goods` and `current_task`.
  - Implement the `Dispatcher` logic in the backend loop.
  - Add AGV states: `PICKING`, `LOADING`, `DELIVERING`, `UNLOADING`.
- **Frontend (`App.tsx`, `SimulatorCanvas.tsx`)**:
  - New ToolMode: `AUTO`.
  - Visual indicators for cargo (orange blocks) on equipment and robots.
  - Task creation UI (First click: Source, Second click: Target).
  - Sidebar update to show the `Waiting List`.

## Success Criteria
1. Selecting a full station then an empty station in AUTO mode correctly queues a task.
2. The nearest standby AGV automatically starts moving to pick up the goods.
3. AGVs wait exactly 5 seconds at stations before cargo is transferred visually and logically.
4. If multiple tasks are waiting, a newly IDLE AGV picks the one closest to its current position.
