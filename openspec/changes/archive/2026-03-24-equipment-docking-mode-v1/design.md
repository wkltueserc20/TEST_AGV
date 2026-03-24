# Design: Equipment Docking Mode

## Architectural Overview
The equipment mode is an extension of the existing obstacle system but adds **identity (ID)** as a primary attribute. 

## Component Details

### 1. Physical Dimensions & Docking
- **Size**: All equipment stars are fixed at **2000mm x 2000mm**. 
- **Docking Point**: The geometric center of the star `(x, y)` acts as the navigation goal.
- **Costmap Integration (Option B Implementation)**: 
  - Center/Core: High cost (`100,000.0`) but NOT infinite.
  - Periphery: Gradient cost to encourage AGVs to stay away unless docking.

### 2. Status & Visual Representation
Equipment nodes now have a `status` attribute that determines their rendering color:
- **`normal` (Normal/Standby)**: Yellow (`#ffd700`) - Ready for task.
- **`running` (Auto/Executing)**: Green (`#39ff14`) - Currently in use (Default for simulation).
- **`error` (Alarm/Fault)**: Red (`#ff4d4d`) - Blocked/Down.

### 3. Rendering Logic
In `frontend/src/SimulatorCanvas.tsx`:
- `drawStar` function will use a 2000mm bounding box.
- The star's fill/stroke color will dynamically update based on `ob.status`.
- Display the ID clearly above or inside the star.

## Data Schema (Equipment Entry)
```json
{
  "id": "Station_Alpha",
  "type": "equipment",
  "status": "running",
  "x": 12000,
  "y": 8000,
  "size": 2000,
  "radius": 1000
}
```

## Risks
- **Goal Reachability**: If the cost is *too* high, some DWA configurations might think the AGV has crashed. We may need to add a "ignore goal cell cost" flag in the planner.
- **ID Collisions**: User could try to rename a node to an existing ID. Need basic validation or error handling.
