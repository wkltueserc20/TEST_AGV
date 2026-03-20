# Tasks: V6.0 UI Refactor Implementation

## Phase 1: Styling & Assets
- [x] Define CSS variables for Dark Mode in `App.css`.
- [x] Apply global dark theme resets to the body and container.
- [x] Update AGV and Path colors to high-contrast "Neon" style.

## Phase 2: Structural Refactoring
- [x] Refactor `App.tsx` layout (used Flexbox for better stability).
- [x] Create `PropertyInspector` for the right sidebar.
- [x] Implement `activeTool` state and the Integrated Toolbar component.

## Phase 3: Advanced Interaction
- [x] Update `SimulatorCanvas` event handlers to respect the `activeTool`.
- [x] Implement Zoom-to-Cursor logic using mouse wheel.
- [x] Implement Panning logic using middle-click or Space+Left-drag.
- [x] Correct coordinate mapping (`canvasToWorld`) to account for Zoom/Pan matrix.

## Phase 4: Data Visualization
- [ ] Implement a basic `Sparkline` component for linear velocity V.
- [ ] Add a visual "Heading Dial" for the selected AGV's Angle.
- [x] Integrate planning status into the UI.
