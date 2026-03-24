# Proposal: Equipment Docking Mode

## Summary
Add a new operation mode to the AGV simulator to manage "Equipment" (Star-shaped nodes). These represent docking stations or physical devices that AGVs can reach but shouldn't drive through unless they are the target.

## Background
Currently, the simulator has rectangles and circles for obstacles. However, in warehouse logistics, we need "Equipment Nodes" which have fixed IDs and represent locations for AGV interaction (docking).

## Goals
- Add a new tool mode `BUILD_STAR` to add/delete equipment.
- Render equipment as **Stars** on the map with their IDs displayed.
- Implement **Option B (Buffer Obstacles)**: High cost at the star center/boundary to discourage "traversing" but allow "docking" (reaching the center).
- Ensure equipment IDs are editable and persistent in `obstacles.json`.

## Technical Scope
- **Backend (`world.py`)**: 
  - Add `equipment` obstacle type.
  - Modify `update_obstacle` to support ID renaming (primary key change).
  - Update `_compute_costmap_task` to use a high-cost (not infinite) penalty for equipment.
- **Frontend (`App.tsx`, `SimulatorCanvas.tsx`)**: 
  - New `ToolMode`: `BUILD_STAR`.
  - Star shape rendering with Canvas.
  - Inspector update: Text input for renaming equipment IDs.

## Success Criteria
1. AGVs planning a path across the map should *avoid* driving through star-shaped equipment.
2. An AGV set to go *to* an equipment's center can successfully plan and reach it.
3. Renaming an equipment ID correctly updates the JSON and UI without losing its position.
