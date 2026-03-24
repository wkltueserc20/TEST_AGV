# Design: UI Rendering Performance Upgrade

## Layering Architecture
We will use a primary visible Canvas and a secondary "Back Buffer" (Offscreen Canvas) to handle different update frequencies.

### 1. Static Buffer (The "Runway")
- **Content**:
  - Background fill (`#0d0e12`).
  - Map boundaries and coordinate grid dots.
  - Static static obstacles (Rectangles and Circles, excluding Equipment).
- **Update Trigger**: Only when the user pans (`offsetX/Y`) or zooms.
- **Implementation**: Draw once to an `OffscreenCanvas` and use `ctx.drawImage()` in the main loop.

### 2. Real-time Overlay (The "Action")
- **Content**:
  - Target markers and pulsing animations.
  - A* search debug trails.
  - Social links and Mission links.
  - AGV bodies and status LEDs.
  - **Equipment Stations** (Option C icons). *Reason: Their status colors change frequently during logistics tasks, and they must stay on top of AGVs.*
- **Update Trigger**: Every `requestAnimationFrame` (synchronized with Telemetry updates).

## Path Rendering Optimization
To further boost performance, the "Path Occupancy" (red repulsion zones) will implement **Skip-Sampling**:
- Instead of drawing a circle for every 200mm path point, we will draw one every **1000mm** (every 5th point) or use a thick `strokePath` logic. This reduces draw calls by 80% without losing visual clarity.

## Event Handling Consistency
Since the coordinate transformation logic (`worldToCanvas` / `canvasToWorld`) remains identical, mouse interactions (click, right-click, double-click) will function exactly as they do now.
