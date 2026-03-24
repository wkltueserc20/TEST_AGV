# Tasks: UI Input Performance Optimization

## Phase 1: Local State Setup
- [x] Refactor `App.tsx` to include `localFields` state (object containing id, x, y, angle).
- [x] Implement a `useEffect` to synchronize `localFields` when `selectedObId` changes or a new telemetry snapshot arrives.
- [x] Add an `isEditing` ref or state to prevent telemetry from overriding local typing.

## Phase 2: Input Integration
- [x] Update **ID** input to use `localFields.id` and commit on blur/Enter.
- [x] Update **X** input to use `localFields.x` and commit on blur/Enter.
- [x] Update **Y** input to use `localFields.y` and commit on blur/Enter.
- [x] Update **ANGLE** input to use `localFields.angle` and commit on blur/Enter.

## Phase 3: Committing Changes
- [x] Centralize the `commitLocalChanges` function to send the `update_obstacle` WebSocket command.
- [x] Ensure coordinate snapping (1000mm) is still applied during commit.

## Phase 4: Verification
- [x] Verify that typing in the fields is instant and smooth.
- [x] Confirm that changes are correctly persisted to the backend and visible on the map after Enter/Blur.
