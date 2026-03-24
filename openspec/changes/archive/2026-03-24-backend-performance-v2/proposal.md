# Proposal: Backend Performance Architecture Upgrade

## Summary
Optimize the backend physics engine by introducing **Geometry Caching** and **Re-planning Throttling**. This eliminates redundant object creations and thread explosions, ensuring smooth performance when multiple AGVs operate simultaneously.

## Background
In the current version (`7cf7359`), the system experiences lag as more AGVs are added. Analysis reveals that:
1. Every AGV recreates all obstacle geometries using Shapely on every sub-step of every frame, causing massive CPU overhead.
2. Sudden path conflicts trigger multiple A* planning threads for the same AGV simultaneously, causing "thread explosion" and GIL contention.

## Goals
- Stable 60FPS simulation even with 5+ AGVs.
- Reduce CPU consumption of the backend process by 70% during movement.
- Maintain 100% functional parity with the existing navigation and docking logic.

## Technical Scope
- **`world.py`**:
  - Implement a geometry cache (`self.obstacle_geoms`) to store pre-calculated Shapely objects.
  - Implement a refresh mechanism triggered by obstacle additions or modifications.
- **`controller.py`**:
  - Update `is_pose_safe` and `compute_command` to use the pre-calculated cache from the world instead of creating objects on-the-fly.
- **`agv.py`**:
  - Enforce strict thread management in `trigger_evasion` and `update` to prevent redundant re-planning.
  - Optimize the collision check sub-steps to be more lightweight for AGV-to-AGV interactions.

## Success Criteria
1. Multiple AGVs can navigate and dock without any visible "hiccups" or speed drops.
2. The number of active threads remains stable even during complex path conflicts.
3. System logs show significantly reduced calculation times for physics updates.
