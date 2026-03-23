## Context

Moving from hardcoded reactive rules to a unified model where evasion is "moving to the nearest coordinates that are outside of everyone's planned trajectory."

## Goals / Non-Goals

**Goals:**
- Consolidate evasion into a "One-Shot" Search -> Plan -> Move flow.
- Ensure targets are outside of the **entire** future path of oncoming traffic.
- Use a strict 2.0m safety margin from walls and paths.

## Decisions

### 1. BFS Safe-Spot Finder (V8 Optimized)
In `planner.py`:
- **Search Method**: BFS with a **25-meter** radius.
- **Safety Criteria**: 
    - `static_costmap == 0` (strictly > 2m from walls).
    - **Circular Exclusion**: Distance to any point in `threat_paths` > 2000mm.
    - **Footprint**: 5x5 grid check (1000x1000mm) must be clear of static walls.
- **Directional Bias**: Filters points that are in the "threat direction" using dot product.

### 2. Full Trajectory Projection
In `agv.py`:
- Moving vehicles update their `path_occupancy` with their **entire** global path.
- This allows idle vehicles to find a spot that is safe for the duration of the threat's mission.

### 3. Social Braking & Wait
- Mission vehicles check if an AGV on their path is in `EVADING` status.
- If so, they **must stop completely** (v=0) to give the evader space.

### 4. Telemetry & Debug Layer
- **Backend**: Broadcast `reserved_havens` mapping.
- **Frontend**: Render a dashed purple circle and an X at the escape destination.

## Risks / Trade-offs

- [Risk] Large BFS search time ➔ Mitigation: Run evasion search in a separate background thread (`_async_replan`).
- [Risk] Deadlock in extremely tight grids ➔ Mitigation: Increase search radius to 25m to find open spaces further away.
