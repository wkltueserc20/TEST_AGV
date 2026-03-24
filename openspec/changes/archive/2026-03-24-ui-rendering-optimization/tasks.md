# Tasks: UI Rendering Performance Upgrade

## Phase 1: Layering Logic
- [x] Create an `offscreenCanvas` ref in `SimulatorCanvas.tsx`.
- [x] Implement `drawStaticLayer` function to render background, grid, and static obstacles.
- [x] Update the main `render` loop to use `ctx.drawImage(offscreenCanvas)` as the first step.
- [x] Implement a cache invalidation mechanism (re-draw static layer when zoom/pan changes).

## Phase 2: Dynamic Content Optimization
- [x] Move AGVs, Paths, and Equipment rendering into the post-static phase.
- [x] Implement path sampling for "Path Occupancy" (every 5th point) to reduce `ctx.arc` calls.
- [x] Ensure `globalAlpha` and `shadowBlur` are correctly managed between layers.

## Phase 3: Verification
- [x] Monitor FPS during multi-AGV movement (target: steady 60 FPS).
- [x] Verify that panning and zooming are responsive.
- [x] Ensure no visual artifacts or Z-index issues (Stars must remain on top).
