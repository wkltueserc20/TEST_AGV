## Context

The V8 architecture treats evasion as a first-class navigation goal. Instead of "moving out of the way," the AGV "moves to a new destination" that happens to be safe from all current and future traffic.

## Goals / Non-Goals

**Goals:**
- **Zero Jitter**: Evasion must be a single, smooth movement.
- **Safety First**: Maintain a strict 2.0m distance from walls and 2.0m from threat trajectories.
- **Decisive Action**: Minimum evasion distance is set to 5.0m to ensure paths are cleared effectively.

## Decisions

### 1. The "Repulsor" Search Algorithm (Planner)
- **Radius**: 25,000mm (25m).
- **Inclusion Criteria**: `static_costmap == 0` AND distance to any threat path node > 2000mm.
- **Geometric Precision**: Uses Euclidean distance for circular buffers instead of square bounding boxes.
- **Search Tiers**: First tries the "Threat-Opposite" direction; falls back to all-around search if the back is a dead end.

### 2. State Machine Hierarchy (AGV)
- `EXECUTING`: High priority. Projects path. Slows down if path is blocked.
- `EVADING`: Mid priority. Moving to a safe spot. Its path is also respected by `EXECUTING` vehicles.
- `IDLE`: Low priority. Monitors environment and initiates `EVADING` if a threat trajectory overlaps its position.

### 3. Intent Broadcasting (World)
- Intent is broadcast as a list of XY coordinates.
- To prevent network lag, the telemetry broadcaster downsamples these points before sending them to the frontend.

### 4. Recovery (Panic Nudge)
- If an AGV is `STUCK` for > 2 seconds, it ignores safety checks for 0.5s and reverses at 100mm/s to break geometric deadlocks.

## Risks / Trade-offs

- [Risk] Large search space might slow down planning ➔ Mitigation: BFS is throttled to 5Hz and runs in a background thread.
- [Risk] Too many points in JSON ➔ Mitigation: Path downsampling implemented in `main.py`.
