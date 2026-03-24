# Design: UI Input Performance Optimization

## Architectural Overview
The core idea is to decouple the **Input View** from the **Global Telemetry State**.

## Component Details

### 1. Local State Buffering
In `App.tsx`, we will introduce a `localObstacleData` state to store transient values:
```typescript
const [localData, setLocalData] = useState({
  id: "",
  x: 0,
  y: 0,
  angle: 0
});
```

### 2. Synchronization Logic
- **Sync-In**: When `selectedObId` changes or `telemetry` is updated *while the user is NOT actively typing*, we update `localData` from the `selectedObstacle` provided by telemetry.
- **Sync-Out**: When an input triggers `onBlur` or `onKeyDown (Enter)`, the `updateObstacle` helper is called with the current `localData` values, pushing the change to the backend.

### 3. Change Propagation
Since the backend broadcast might take a few milliseconds, we use the local state as the "source of truth" for the input's `value` attribute. This ensures the cursor doesn't jump and the characters appear instantly.

## UI/UX Improvements
- All numeric inputs will support `step="1000"` for coordinates and `step="1"` for angles.
- Pressing `Enter` in any field will automatically commit the change and unfocus the input (or keep focus but sync).

## Risks
- **Overwriting Sync**: If an AGV moves an obstacle (dynamic obstacles), the telemetry might update while we are typing. We need a flag or check to prevent telemetry from overwriting `localData` during active editing.
