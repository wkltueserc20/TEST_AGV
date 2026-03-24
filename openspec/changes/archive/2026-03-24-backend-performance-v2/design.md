# Design: Backend Performance Architecture Upgrade

## Core Components

### 1. Geometry Caching (World Class)
Instead of passing a simple list of obstacle dictionaries, the `World` will maintain a dictionary of `Shapely` objects.
- **Cache Definition**: `self.obstacle_geoms = { "OB_ID_1": Shapely.Geometry, ... }`
- **Cache Refresh**: 
  - `load_obstacles()`: Full rebuild.
  - `add_obstacle()`: Single add.
  - `update_obstacle()`: Single update.
  - `remove_obstacle()`: Single delete.
- **Benefit**: Removes the need for `box()`, `rotate()`, `translate()`, and `Point().buffer()` in the high-frequency physics loop.

### 2. Optimized Collision Checking (Controller Class)
The `is_pose_safe` method will be updated to:
1. Accept the `world` object or the cached `geoms` dictionary.
2. Iterate through cached static geoms for 0-overhead intersection checks.
3. Dynamically create geoms ONLY for other moving AGVs (since their poses change every frame).

### 3. Thread Management (AGV Class)
The `trigger_evasion` method is currently the main source of thread explosion.
- **New Logic**:
  ```python
  def trigger_evasion(self, world):
      if self.is_planning:
          return # Already working on a new path, do not spawn another thread
      # ... proceed to spawn thread
  ```
- **Benefit**: Ensures a maximum of 1 planning thread per AGV at any given time.

## Data Flow
`World` updates data ➔ `World` refreshes Cache ➔ `AGV` calls `Controller` ➔ `Controller` queries `World` Cache ➔ Instant Result.

## Risks
- **Cache Invalidation**: If an obstacle is updated but the cache isn't refreshed, collision results will be wrong. We must wrap all obstacle modifiers with a cache refresh call.
