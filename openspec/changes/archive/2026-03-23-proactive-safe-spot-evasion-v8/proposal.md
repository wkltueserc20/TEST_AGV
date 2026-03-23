## Why

The V7 reactive logic was prone to oscillations and "suicidal evasion" in narrow corridors. This V8 upgrade transitions the system to a **Proactive One-Shot Evasion** model. By broadcasting full mission trajectories and identifying safe spots far from any future threat, we eliminate jittery movements and ensure traffic flows smoothly without constant re-planning.

## What Changes

- **Full-Trajectory Projection**: Moving AGVs broadcast their entire remaining path to the World occupancy map.
- **One-Shot Decision Locking**: Idle AGVs trigger a single, decisive evasion maneuver to a distant safe spot and lock that status until arrival.
- **Circular Threat Zones**: Improved threat detection using a precise 2.0m circular radius to prevent over-evasion in diagonal paths.
- **Hierarchical Social Braking**: Mission vehicles now wait completely (v=0) for any AGV currently in `EVADING` status.
- **Performance Downsampling**: Telemetry data is downsampled (1/3 for paths, 1/5 for occupancy) to maintain 60FPS visuals during multi-AGV scenarios.

## Capabilities

### New Capabilities
- `safe-spot-search`: High-performance BFS with 25m range, circular exclusion, and 1000mm footprint validation.
- `directional-locking`: State machine logic that prevents interruption of active evasion tasks.

### Modified Capabilities
- `telemetry-broadcast`: Adaptive downsampling for high-density path data.

## Impact

- `backend/agv.py`: Central logic for state transitions and intent broadcasting.
- `backend/planner.py`: Optimized BFS and A* with trajectory awareness.
- `backend/main.py`: Synchronized telemetry broadcasting.
