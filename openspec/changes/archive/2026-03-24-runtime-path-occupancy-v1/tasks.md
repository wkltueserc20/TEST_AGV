# Tasks: Run-time Path Occupancy Publishing

## Implementation
- [x] Modify `AGV.update` in `backend/agv.py` to condition `update_path_occupancy` on `self.is_running`.
- [x] Ensure `clear_path_occupancy` is called when the AGV stops or finishes.

## Verification
- [x] Verify AGV-A path doesn't scare AGV-B before START.
- [x] Verify AGV-B evades as soon as AGV-A starts.
- [x] Verify red circles disappear when mission finishes.
