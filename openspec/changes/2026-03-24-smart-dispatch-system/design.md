# Design: Smart Logistics Dispatch System

## Proximity-Based Dispatch Logic
When an AGV's state changes to `IDLE`:
1. Iterate through all tasks in the `Waiting List`.
2. Calculate the distance from the AGV's current $(x, y)$ to each task's **Source Station** $(sx, sy)$.
3. Select the task with the minimum distance.
4. Assign task to AGV and remove it from the `Waiting List`.

## AGV State Machine
- **IDLE**: Ready for tasks.
- **PICKING**: Navigation to Source Station. Using docking logic.
- **LOADING**: 
  - Starts when distance to Source < 300mm and angle aligned.
  - `v=0`, `omega=0`.
  - Timer: 5 seconds.
  - End: Source `has_goods = False`, AGV `has_goods = True`.
- **DELIVERING**: Navigation to Target Station. Using docking logic.
- **UNLOADING**:
  - Starts when distance to Target < 300mm and angle aligned.
  - `v=0`, `omega=0`.
  - Timer: 5 seconds.
  - End: Target `has_goods = True`, AGV `has_goods = False`.

## UI/UX: AUTO Mode Interaction
- **State 1**: User clicks an equipment with `has_goods = True`. Store as `pendingSource`.
- **State 2**: User clicks an equipment with `has_goods = False`. 
- **Action**: Call `dispatch_task(sourceId, targetId)`. Reset selection states.

## Visualization
- **Cargo**: An orange cube (e.g., `#ff9800`) drawn at the center of the station icon or AGV body.
- **Queue**: Displayed in the sidebar as a list of `Source -> Target`.
