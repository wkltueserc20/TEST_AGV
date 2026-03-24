# Design: Run-time Path Occupancy Publishing

## Logic Refinement
In `backend/agv.py`, the `update` method currently checks `if self.global_path` to decide whether to call `world.update_path_occupancy`.

This will be changed to:
```python
if self.global_path and self.is_running:
    # Update occupancy (Show red circles, trigger evasion in others)
else:
    # Clear occupancy (Others are safe)
```

## Side Effects
- This change will also hide the "red translucent circles" on the frontend for idle AGVs, which is consistent with the "not a threat" status.
- Social Links (waiting/yielding lines) might still appear if we use `is_pose_safe` check, but the proactive "chasing" will definitely stop.
