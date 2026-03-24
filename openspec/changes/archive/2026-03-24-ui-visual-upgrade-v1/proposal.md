# Proposal: Equipment Iconography & AGV Visual Fixes

## Summary
Upgrade the equipment visual from a simple star to a professional "Industrial Workstation" icon (Option C). Additionally, restore the missing AGV status LED indicators to provide clear operational feedback.

## Background
The current star icon for equipment is too generic. In industrial simulation, a specialized station icon is preferred. Also, a previous refactor accidentally removed the LED lights from the AGV body, making it hard to see the current state (Running/Planning/Idle) without checking the sidebar.

## Goals
- Replace the `drawStar` logic with a dedicated SVG-based **Industrial Workstation** symbol.
- Maintain the **2000mm x 2000mm** physical size for the icon.
- Restore the **AGV Status LED** at the top-left of each robot.
- Ensure the icon colors reflect the equipment status (Normal: Yellow, Running: Green, Error: Red).

## Technical Scope
- **Frontend (`SimulatorCanvas.tsx`)**:
  - Define an SVG Path for the "Factory/Workstation" symbol.
  - Implement `ctx.fill(new Path2D(svgPath))` rendering for high performance.
  - Re-inject the LED rendering code into the AGV drawing loop.
  - Re-align the Docking Arrow and ID text to center properly on the new icon.

## Success Criteria
1. Equipment appears as professional industrial symbols instead of stars.
2. AGVs show a glowing green/orange/red LED based on their mission status.
3. The visual hierarchy (Z-Index) remains correct (Equipment on top).
