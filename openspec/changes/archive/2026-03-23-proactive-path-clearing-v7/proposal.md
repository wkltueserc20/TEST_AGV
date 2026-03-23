## Why

The current reactive evasion logic causes logic oscillations and deadlocks in tight corners and narrow corridors. AGVs only attempt to yield after a conflict has already occurred, often leading to geometric traps where neither vehicle has enough space to maneuver. A proactive approach is needed where non-task vehicles clear the path *before* task-executing vehicles arrive.

## What Changes

- **BREAKING**: Remove the legacy decentralized priority arbitration and `culprit_id` based yielding logic.
- **Intent Projection**: Active AGVs will now broadcast their future path segments as "Repulsion Zones".
- **Proactive Evasion**: Standby/Idle AGVs will monitor these zones. If they detect a future collision with an active path, they will proactively move to the nearest "Neutral Spot" (Haven).
- **Simplified State Machine**: Re-architect the AGV states into four clear modes: `IDLE` (monitoring), `EXECUTING` (task), `EVADING` (moving to clear path), and `STUCK` (emergency recovery).
- **Sub-stepping Physics**: Maintain the recently implemented sub-stepping for smooth high-speed simulation.

## Capabilities

### New Capabilities
- `path-projection`: Moving AGVs project their intended trajectory into a shared occupancy map in the World.
- `proactive-evasion`: Idle AGVs detect occupancy conflicts and seek safe temporary positions.

### Modified Capabilities
- `swarm-intelligence`: Shifting from reactive social intelligence to a hierarchy-based path clearing model.

## Impact

- `backend/world.py`: Add path occupancy tracking.
- `backend/agv.py`: Rewrite update loop and state transitions.
- `backend/controller.py`: Refine path following and nudge logic.
- `backend/main.py`: Update snapshot to reflect new state types.
