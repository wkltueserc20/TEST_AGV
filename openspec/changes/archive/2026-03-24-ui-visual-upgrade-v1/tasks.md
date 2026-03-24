# Tasks: Equipment Iconography & AGV Visual Fixes

## Phase 1: AGV LED Restoration
- [x] Locate the AGV drawing loop in `SimulatorCanvas.tsx`.
- [x] Re-implement the LED indicator at the top-left of the chassis.
- [x] Add the glowing/shadow effect for the active state.

## Phase 2: Equipment Icon Upgrade
- [x] Define the `stationPath` constant in `SimulatorCanvas.tsx`.
- [x] Replace `drawStar` function with an SVG Path-based rendering logic.
- [x] Scale the path to match the **2000mm x 2000mm** physical footprint.
- [x] Ensure the icon is drawn with 0.7 alpha and correct status colors.

## Phase 3: Alignment & Polish
- [x] Verify the **Docking Arrow** is centered relative to the new station icon.
- [x] Verify the **ID Text** position is still clear.
- [x] Test the mission states to confirm LED color accuracy.
