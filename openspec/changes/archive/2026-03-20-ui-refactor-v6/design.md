# Design: Professional Workstation Architecture

## 1. Component Structure
The flat `App.tsx` will be broken into a hierarchy of specialized components:

```text
App
├── Header (Project Info, Global Simulation Control)
├── MainContainer (Grid Layout)
│   ├── LeftSidebar (Fleet List, Obstacle Count, Global Algorithm Settings)
│   ├── CanvasViewport (The SimulatorCanvas with Toolbar Overlay)
│   │   └── FloatingToolbar (Select, Build, Nav tool icons)
│   └── RightSidebar (Property Inspector: AGV/Obstacle details, Telemetry graphs)
└── Footer (Status bar: Connectivity, FPS, Costmap status)
```

## 2. State Management
- **`activeTool`**: Enum (`'select'`, `'build-sq'`, `'build-cir'`, `'nav'`) controlling canvas interaction.
- **Telemetry History**: A sliding window buffer (e.g., last 100 packets) to support real-time sparklines.
- **Canvas Matrix**: A `viewMatrix` state managing `scale`, `offsetX`, and `offsetY` for panning/zooming.

## 3. Visual Styling (CSS Variables)
Transition to a CSS variable-based system for effortless theme switching:
```css
:root {
  --bg-primary: #121212;
  --bg-secondary: #1e1e1e;
  --text-main: #e0e0e0;
  --accent-blue: #007bff;
  --accent-glow: rgba(0, 123, 255, 0.3);
}
```

## 4. Canvas Rendering Logic
The `SimulatorCanvas` will be updated to apply a 2D transform matrix before rendering all elements:
1. `ctx.save()`
2. `ctx.translate(offsetX, offsetY)`
3. `ctx.scale(zoom, zoom)`
4. Render Path, Search Cloud, Obstacles, AGVs.
5. `ctx.restore()`
6. (Optional) Overlay UI elements that don't scale.
