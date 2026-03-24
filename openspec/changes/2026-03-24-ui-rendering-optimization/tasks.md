# Tasks: UI Rendering Performance Upgrade

## Phase 1: Layering Logic
- [ ] Create an `offscreenCanvas` ref in `SimulatorCanvas.tsx`.
- [ ] Implement `drawStaticLayer` function to render background, grid, and static obstacles.
- [ ] Update the main `render` loop to use `ctx.drawImage(offscreenCanvas)` as the first step.
- [ ] Implement a cache invalidation mechanism (re-draw static layer when zoom/pan changes).

## Phase 2: Dynamic Content Optimization
- [ ] Move AGVs, Paths, and Equipment rendering into the post-static phase.
- [ ] Implement path sampling for "Path Occupancy" (every 5th point) to reduce `ctx.arc` calls.
- [ ] Ensure `globalAlpha` and `shadowBlur` are correctly managed between layers.

## Phase 3: Verification
- [ ] Monitor FPS during multi-AGV movement (target: steady 60 FPS).
- [ ] Verify that panning and zooming are responsive.
- [ ] Ensure no visual artifacts or Z-index issues (Stars must remain on top).
