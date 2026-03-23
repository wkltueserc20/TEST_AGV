## Why

The current multi-AGV evasion logic is fragmented into numerous special cases, making it difficult to maintain. This change simplifies the system by consolidating all evasion into a single flow: proactively find an absolute "safe spot" that doesn't conflict with anyone else's **full** projected path, then use the robust A* planner to navigate there.

## What Changes

- **BREAKING**: Removed legacy reactive evasion methods (`check_proactive_evasion`, `trigger_evasion`, etc.).
- **Full Path Intent Broadcast**: Moving AGVs now broadcast their **entire remaining trajectory** instead of just a short segment.
- **Unified Safe-Spot Search**: Implemented a BFS-based search in the planner to find the nearest point that is physically safe (cost=0) and does not intersect with any other AGV's full trajectory (using a **2.0m circular buffer**).
- **A* Driven Evasion**: Evasion is treated as a standard navigation task to a temporary "Safe Spot" target.
- **One-Shot Locking**: Once an AGV starts evading, it locks its target until arrival to prevent jittery oscillations.
- **Evasion Visualization**: Render the "Safe Spot" target (purple X) on the canvas for debugging.

## Capabilities

### New Capabilities
- `safe-spot-search`: BFS algorithm with 25m range and footprint validation.
- `evasion-visualization`: Real-time rendering of `reserved_havens`.

### Modified Capabilities
- `swarm-intelligence`: Goal-oriented proactive model using full path projection.

## Impact

- `backend/agv.py`: Rewrite evasion trigger and state transitions.
- `backend/planner.py`: Add `find_nearest_safe_spot` with circular exclusion.
- `backend/main.py`: Broadcast `reserved_havens`.
