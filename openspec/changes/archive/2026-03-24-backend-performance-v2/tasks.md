# Tasks: Backend Performance Architecture Upgrade

## Phase 1: Core Geometry Caching (World)
- [x] Add `self.obstacle_geoms` cache dictionary to `World` class in `world.py`.
- [x] Implement `refresh_obstacle_geometries()` to pre-calculate Shapely objects.
- [x] Update `load_obstacles`, `add_obstacle`, `update_obstacle`, and `remove_obstacle` to trigger cache refresh.

## Phase 2: Controller Optimization
- [x] Update `is_pose_safe` in `controller.py` to use `world.obstacle_geoms`.
- [x] Update `compute_command` method signature and internal calls to support the new cache system.
- [x] Ensure dynamic obstacles (AGVs) are still handled correctly without caching.

## Phase 3: Thread & Loop Optimization (AGV)
- [x] Add `if self.is_planning: return` check to `trigger_evasion` in `agv.py`.
- [x] Optimize `AGV.update` to pass the `world` object instead of the raw obstacle list to the controller.
- [x] Review all `math.sqrt` calls in `agv.py` and replace with squared comparisons where missed.

## Phase 4: Verification & Cleanup
- [x] Verify multi-AGV fluid movement in the frontend.
- [x] Ensure all manual and logistics functions (A ➔ B tasks) remain operational.
- [x] Remove any leftover debugging code or redundant calculations.
