# Proposal: UI Input Performance Optimization

## Summary
Implement local state buffering for all input fields in the Inspector (ID, X, Y, Angle). This eliminates input lag caused by immediate WebSocket synchronization and global re-renders.

## Background
Currently, input fields in the settings panel trigger a WebSocket update on every keystroke (`onChange`). This results in a full application re-render, including the heavy Canvas component, making the typing experience extremely sluggish.

## Goals
- Eliminate input lag by using local React state for uncommitted changes.
- Ensure the UI feels responsive (instant character feedback).
- Synchronize data with the backend only when the user has finished editing.

## Technical Scope
- **Frontend (`App.tsx`)**:
  - Extend the local state buffering mechanism (currently only for `editingId`) to include `x`, `y`, and `docking_angle`.
  - Bind all input `onChange` handlers to local state.
  - Implement `onBlur` and `onKeyDown (Enter)` triggers to send the `update_obstacle` command to the backend.
  - Ensure local states are synchronized when a different obstacle is selected.

## Success Criteria
1. Typing or changing numbers in X, Y, or ANGLE fields results in instant UI updates without any lag.
2. The backend is updated correctly once the user navigates away from the field or presses Enter.
3. No "state fighting" occurs (server updates overwriting local typing state).
