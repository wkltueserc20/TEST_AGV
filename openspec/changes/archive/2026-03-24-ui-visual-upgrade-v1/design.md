# Design: Equipment Iconography & AGV Visual Fixes

## Component Details

### 1. The Industrial Workstation Icon (Option C)
The new icon will be rendered using a constant SVG path string. It represents an overhead view of an automated factory cell.
- **SVG Path Definition**:
  `M -50,-50 L 50,-50 L 50,-20 L 40,-20 L 40,20 L 50,20 L 50,50 L -50,50 L -50,20 L -40,20 L -40,-20 L -50,-20 Z`
  (A rectangle with side notches for a more "mechanical" feel).
- **Scale**: Normalized to 100 units, then scaled by the `radius` (1000mm) to achieve the 2m x 2m size.

### 2. AGV Status LED
Restoring the triple-color LED logic:
- Position: Top-left corner of the AGV chassis (`-sz/2 + 15, -sz/2 + 15`).
- Logic:
  - `is_running` -> Glowing Green (`#00ff00`)
  - `is_planning` -> Blinking Orange (`#ffc107`)
  - `Idle` -> Red (`#ff3333`)

### 3. Rendering Order (Z-Index Refinement)
1.  Target Markers
2.  Path Repulsion Zones
3.  Planned Paths (Dashed Lines)
4.  Static Obstacles (Rect/Circle)
5.  AGV Bodies (with restored LEDs)
6.  **Equipment Icons** (Highest layer, translucent fill)

## UI Consistency
- The docking direction arrow will be centered on the new icon.
- Hovering or selecting the icon will still apply the orange highlight and glow.
