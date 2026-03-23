# Design: Social Intelligence Architecture

## 1. Decentralized Diagnosis Logic
The `AGVController` will be updated to return a `Tuple[float, float, str]` where the third element is the `culprit_id`.

```python
# In controller.py
def is_pose_safe(self, ..., obstacles):
    for ob in obstacles:
        if poly.intersects(ob_geom):
            return False, ob.get("id") # Returns the specific ID
```

## 2. Escape Planner: Intersection BFS
When an AGV needs to yield but lateral movement is blocked (Corridor Case):
1. **Grid Sampling**: Samples grid points within a 5m radius.
2. **Intersection Detection**: A point is an intersection if it has >2 navigable neighbors in the `static_costmap`.
3. **Safety Scoring**: Candidates are ranked by `distance` and `path_distance_from_guest`.
4. **Temporary Target**: The best candidate becomes the AGV's target in `YIELDING` state.

## 3. Dynamic Priority System
A score $P$ is calculated per update cycle:
$$P = TaskFactor + ProgressFactor + (WaitTime \times 0.1)$$
- $TaskFactor$: 50 for MOVING, 0 for IDLE.
- $WaitTime$: Seconds since velocity became 0 while status was MOVING.

## 4. Social UI Layer
- **Status Link**: A `relationship` object in telemetry: `{"from": "AGV-A", "to": "AGV-B", "type": "WAITING"}`.
- **Canvas Rendering**: Draw a dashed line between the pair. Render a "Haven Icon" (淡紫色 X) at the escape destination.
