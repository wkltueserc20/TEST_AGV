# Proposal: UI Rendering Performance Upgrade

## Summary
Optimize the simulator's rendering engine by implementing a **Dual-Layer Canvas** system. This decouples static background elements (grid, boundaries) from dynamic real-time objects (AGVs, paths), significantly reducing CPU/GPU overhead during multi-AGV movement.

## Background
Currently, the `SimulatorCanvas` redraws every single element—including hundreds of grid dots—on every frame (60 FPS). As the number of AGVs and path points increases, the time required to clear and redraw the entire map causes noticeable lag and frame drops.

## Goals
- Achieve a stable **60 FPS** even with 10+ AGVs moving simultaneously.
- Eliminate visual jitter during map panning and zooming.
- Reduce CPU usage of the frontend application.

## Technical Scope
- **Frontend (`SimulatorCanvas.tsx`)**:
  - Implement an **Offscreen Canvas** or a secondary hidden `<canvas>` to cache the static background.
  - Split the `render` loop into `renderStatic` (Grid, Map Border, Non-equipment Obstacles) and `renderDynamic` (AGVs, Paths, Task Links, Equipment).
  - Use `requestAnimationFrame` more efficiently by only redrawing the dynamic layer when telemetry updates.
- **Optimization**: Implement path sampling for "Path Occupancy" circles to reduce the number of draw calls.

## Success Criteria
1. The simulator remains fluid (no stuttering) when multiple AGVs are navigating and docking.
2. The "blunting" or "delay" felt during mouse interaction is eliminated.
3. Visual output remains identical to the current professional industrial style.
