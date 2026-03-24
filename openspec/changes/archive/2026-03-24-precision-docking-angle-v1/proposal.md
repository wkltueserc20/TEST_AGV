# Proposal: Precision Docking Angle for Equipment

## Summary
Add a "Docking Angle" setting to equipment nodes. This allows users to define the exact heading an AGV should have when it reaches the equipment center. The path planner will be updated to ensure AGVs approach from the correct direction to achieve this final pose.

## Background
Currently, AGVs reach the center of equipment with a random heading depending on the last leg of the A* path. For industrial docking (e.g., picking up a pallet), a consistent and precise entry angle is required.

## Goals
- Add a configurable `docking_angle` attribute to each equipment.
- Display a directional arrow on equipment stars in the simulator.
- Implement **Option A (Waypoint Injection)** in the path planner to force a straight-line approach from the specified angle.
- Ensure AGVs complete missions only when both position and heading are aligned.

## Technical Scope
- **Data (`obstacles.json`)**: Add `docking_angle` (0-359 degrees) to equipment objects.
- **Frontend (`App.tsx`, `SimulatorCanvas.tsx`)**: 
  - Add numeric input for angle in the Inspector.
  - Render a "Heading Arrow" on the equipment star.
- **Backend (`planner.py`)**: 
  - If the goal is an equipment center, calculate an "approach point" 1500mm away in the direction opposite to the docking angle.
  - Force the path to pass through this approach point before the final goal.
- **Backend (`agv.py`)**: 
  - Update movement completion logic to check for heading alignment.

## Success Criteria
1. An AGV navigating to an equipment set at 90° always enters from the bottom and stops facing up.
2. The docking angle is persistent and can be modified in real-time.
3. Path planning avoids obstacles while respecting the mandatory approach vector.
