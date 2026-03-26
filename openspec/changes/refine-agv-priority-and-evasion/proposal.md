## Why

Idle AGVs currently have the same priority as moving AGVs in SINGLE mode, leading to situations where a moving AGV is blocked by an idle one if the idle AGV has a larger ID. This change ensures that idle AGVs always yield to those that are executing tasks or moving, and refines the tie-breaker logic.

## What Changes

- **Priority Logic Refinement**: Update `get_priority` to assign higher priority (lower numerical value) to AGVs in `EXECUTING` or `PLANNING` states compared to those in `IDLE`.
- **Conflict Resolution Arbitration**: Modify the ID-based tie-breaker in `check_proactive_evasion` so that larger ID AGVs consistently yield to smaller ID ones when priorities are equal.
- **Enhanced Evasion Triggering**: Ensure idle AGVs proactively trigger evasion when they detect a conflict with a higher-priority moving AGV.

## Capabilities

### New Capabilities
- `agv-behavior-priority`: Refined priority rules and conflict resolution for heterogeneous AGV states.

### Modified Capabilities
- None

## Impact

- `backend/agv.py`: Modification to `get_priority` and `check_proactive_evasion`.
- System-wide traffic flow and deadlock prevention.
