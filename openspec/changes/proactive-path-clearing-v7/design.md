## Context

The current reactive system relies on detecting collisions after they enter safety margins. This design shifts responsibility to the **Standby** vehicles to proactively clear the path for **Active** vehicles. By sharing intended path segments, we create a "dynamic repulsion" field that prevents vehicles from ever getting too close in narrow areas.

## Goals / Non-Goals

**Goals:**
- Move idle AGVs out of the way *before* a task AGV arrives.
- Simplify state transitions by removing complex social priority arbitration.
- Use path projection to define "Repulsion Zones".
- Support backwards movement as a primary evasion strategy.

**Non-Goals:**
- Implementing a centralized traffic controller (TC).
- Optimizing A* for multi-agent coordination (we rely on spatial evasion).

## Decisions

### 1. Path Occupancy Registry
The `World` class in `backend/world.py` will host a shared registry of active paths.
- **Data Structure**: `self.path_occupancy = { agv_id: List[Tuple[float, float]] }`
- **Update Frequency**: Every moving AGV updates its occupancy segment at 20Hz (within its update loop).
- **Segment Length**: Only the next ~3000mm (approx. 15-20 nodes) of the path are projected to avoid over-constraining the map.

### 2. Proactive Evasion Trigger
Instead of checking `culprit_id` from the controller, an `IDLE` AGV will perform its own check:
```python
def check_proactive_evasion(self, world):
    my_circle = Point(self.x, self.y).buffer(1200) # Social radius
    for other_id, path_points in world.path_occupancy.items():
        if other_id == self.id: continue
        # Check if any projected point enters my social radius
        for px, py in path_points:
            if my_circle.contains(Point(px, py)):
                self.trigger_evasion(world)
                return
```

### 3. "The Moving Vehicle Does Not Move" Rule
- If an AGV is in `EXECUTING` (Task) state and gets blocked, it simply stops and waits. It **does not** yield.
- If an AGV is `IDLE` and detects an oncoming path, it **must** yield.
- This hierarchy eliminates the "both vehicles trying to turn around" problem.

### 4. Backwards-First Evasion
The `trigger_evasion` logic will prioritize:
1. Reversing 2000mm along its own current path (if it has one).
2. BFS search for nearest intersection (Haven) that is NOT in the `path_occupancy` map.

## Risks / Trade-offs

- [Risk] Performance hit from occupancy checks ➔ Mitigation: Only check next 15 points of other paths; use spatial hashing if fleet size grows.
- [Risk] Evasion loops (A moves for B, B then moves for A) ➔ Mitigation: Only `IDLE` vehicles can be repelled. Once in `EVADING` state, the vehicle has a temporary path that is also projected, but with lower "repulsion priority".
- [Risk] Stale paths in registry ➔ Mitigation: World automatically clears entries if AGV stops moving or disconnects.
