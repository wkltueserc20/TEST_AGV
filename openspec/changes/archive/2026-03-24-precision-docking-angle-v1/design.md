# Design: Precision Docking Angle

## Architectural Overview
This feature modifies the Path Planning pipeline by post-processing the A* result to include a mandatory "Approach Vector".

## Component Details

### 1. Data Model Extension
Equipment nodes in `obstacles.json` will now include:
```json
{
  "id": "Station_01",
  "type": "equipment",
  "docking_angle": 90, // Degrees (0 = Right, 90 = Up, 180 = Left, 270 = Down)
  ...
}
```

### 2. Path Planning (Option A: Waypoint Injection)
In `backend/planner.py`, the `get_path` function will be updated:
1. Identify if the `goal` corresponds to an equipment node.
2. If yes, retrieve its `docking_angle` (converted to radians $\theta$).
3. Calculate the **Approach Point** $(x_a, y_a)$:
   - $x_a = x_{center} - 1500 \cdot \cos(\theta)$
   - $y_a = y_{center} - 1500 \cdot \sin(\theta)$
4. Perform A* search from `start` to $(x_a, y_a)$.
5. Append the final `center` point to the resulting path.
   - Resulting Path: `[Path_to_Approach_Point] + [Center_Point]`

### 3. Rendering
In `frontend/src/SimulatorCanvas.tsx`:
- Render a **Directional Arrow** inside or near the equipment star.
- The arrow points in the direction of `docking_angle`.
- Color: High-contrast white or cyan to indicate "Active Entry Vector".

### 4. Controller Adjustment
In `backend/agv.py`, the "Goal Reached" check will be updated:
- Current: `Distance < 300mm`
- New: `Distance < 300mm AND Angle_Error < 5 degrees`
- If the angle is not yet aligned, the AGV should perform a final in-place rotation to the `docking_angle`.

## UI/UX
- The Sidebar Inspector will detect when an equipment is selected and show an "Angle" numeric input.
- Users can input values from 0 to 359.

## Risks
- **Approach Point in Obstacle**: If an equipment is placed too close to a wall (distance < 1500mm from the entry side), the approach point might be unreachable.
- **Planner Logic**: If A* fails to reach the approach point, the AGV should fallback to standard A* to at least reach the center.
