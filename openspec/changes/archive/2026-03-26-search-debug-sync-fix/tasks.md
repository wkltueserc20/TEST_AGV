## 1. Backend Optimization & Synchronization

- [x] 1.1 Update `AGV.to_dict()` in `backend/agv.py` to remove the condition that hides `visited` nodes when `is_running` is true.
- [x] 1.2 Implement sparse sampling logic in `to_dict()` to take every 5th node from `self.visited_nodes`.
- [x] 1.3 Implement a hard cap of 1000 nodes for the sampled `visited` list in `to_dict()` to optimize bandwidth.

## 2. Verification & Validation

- [ ] 2.1 Launch the simulation and dispatch a long-distance task to an AGV.
- [ ] 2.2 Verify that the Search Debug Layer (blue nodes) begins its "revealing" animation as soon as the red path appears, while the AGV is still at the start or in transit.
- [ ] 2.3 Confirm that the animation completes correctly and represents the search area used for the current path.
- [ ] 2.4 Verify that multiple AGVs moving simultaneously does not cause noticeable lag in the UI or telemetry updates.
