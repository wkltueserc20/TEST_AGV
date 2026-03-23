## Why

The current multi-AGV evasion logic is fragmented into numerous special cases (reversing, junction searching, social braking), making it difficult to maintain and prone to geometric deadlocks. This change simplifies the system by consolidating all evasion into a single flow: proactively find a "safe spot" that doesn't conflict with anyone else's projected path, then use the robust A* planner to navigate there.

## What Changes

- **BREAKING**: Remove legacy reactive evasion methods (`check_proactive_evasion`, `trigger_evasion`, etc.) from the AGV class.
- **Unified Safe-Spot Search**: Implement a centralized BFS-based search in the planner to find the nearest point that is physically safe and does not intersect with any other AGV's projected trajectory.
- **A* Driven Evasion**: Instead of custom "reversing" or "offsetting" logic, evasion is now treated as a standard navigation task to a temporary "Safe Spot" target.
- **Proactive Execution**: AGVs scan for future path conflicts and trigger evasion before the threat enters immediate safety margins.
- **Evasion Visualization**: Render the "Safe Spot" target on the canvas for easier debugging and transparency.

## Capabilities

### New Capabilities
- `safe-spot-search`: Efficient BFS algorithm to find unoccupied, non-threatened map locations.
- `evasion-visualization`: Real-time rendering of evasion targets in the frontend.

### Modified Capabilities
- `swarm-intelligence`: Transitioning from a rule-based reactive model to a goal-oriented proactive model.

## Impact

- `backend/agv.py`: Rewrite evasion trigger and state transitions.
- `backend/planner.py`: Add `find_nearest_safe_spot` utility.
- `backend/main.py`: Update telemetry snapshot to include evasion targets.
- `frontend/src/SimulatorCanvas.tsx`: Render evasion markers.
