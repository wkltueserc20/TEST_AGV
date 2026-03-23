## Context

The system currently uses a mix of hardcoded evasion strategies (reverse 5m, find junction). This leads to brittle behavior in complex layouts. We are moving to a unified model where evasion is simply "moving to the nearest safe coordinates" using the existing A* navigation pipeline.

## Goals / Non-Goals

**Goals:**
- Consolidate evasion logic into a single "Search -> Plan -> Move" flow.
- Ensure evasion targets are physically valid (using the 1000x1000mm footprint).
- Proactively trigger evasion based on projected path overlaps.
- Visualize evasion targets for debugging.

**Non-Goals:**
- Modifying the underlying A* implementation (we use it as-is).
- Implementing a centralized traffic manager (logic remains decentralized).

## Decisions

### 1. BFS Safe-Spot Finder
In `planner.py`, we will implement `find_nearest_safe_spot(start_pos, static_costmap, threat_paths)`:
- **Search Method**: Breadth-First Search starting from the AGV's current grid cell.
- **Safety Criteria**: 
    - No intersection with `static_costmap` (wall/obstacle).
    - No intersection with any point in `threat_paths` (projected trajectories of other AGVs).
    - Grid cell must accommodate the 1000x1000mm footprint (3x3 grid cells).
- **Radius**: Search up to 10 meters from origin.

### 2. State Machine Simplification
The AGV states will be strictly:
- `IDLE`: Not moving, monitoring for repulsion.
- `MISSION`: Moving toward a user-defined goal.
- `EVADING`: Moving toward a temporary safe spot.
- `STUCK`: No path found or blocked by physical geometry.

### 3. Unified Evasion Loop
In `agv.update`, the logic becomes:
```python
if self.status in [IDLE, EVADING]:
    if self.is_conflicted(world):
        safe_spot = planner.find_nearest_safe_spot(...)
        if safe_spot:
            self.set_target(safe_spot, status=EVADING)
```

### 4. Telemetry & Debug Layer
- **Backend**: Add `evasion_target` to `AGV.to_dict()`.
- **Frontend**: Update `SimulatorCanvas.tsx` to render a specific marker (e.g., a dashed purple circle) at the `evasion_target` when the AGV is in `EVADING` state.

## Risks / Trade-offs

- [Risk] BFS search performance in high-speed simulation ➔ Mitigation: Throttle the search to 5Hz or 10Hz; the physics loop remains high-frequency.
- [Risk] Evasion ping-pong (A moves for B, B then moves for A) ➔ Mitigation: Maintain the priority hierarchy where `MISSION` vehicles have right-of-way over `IDLE`/`EVADING` vehicles.
