## Context

The current `get_priority` in `backend/agv.py` assigns priority 100 to any AGV without a task. In SINGLE mode, moving AGVs do not have a `current_task`, so they are treated as equal to idle AGVs. When priorities are equal, `check_proactive_evasion` forces the smaller ID AGV to yield. This causes an idle large-ID AGV to block a moving small-ID AGV.

## Goals / Non-Goals

**Goals:**
- Make moving/executing AGVs always have higher priority than truly idle ones.
- Establish a consistent tie-breaker where the larger ID yields to the smaller ID.
- Ensure proactive evasion works correctly for manual (SINGLE) moves.

**Non-Goals:**
- Changing the A* planning algorithm.
- Modifying the DWA controller.
- Changing the UI interaction modes.

## Decisions

### 1. Refined Priority Assignment
- **Decision**: Update `get_priority` to return:
    - `0` for critical task/loading/unloading.
    - `5` for active `current_task`.
    - `50` for `EXECUTING` or `PLANNING` states (even without a task, for SINGLE mode).
    - `100` for `IDLE` or `STUCK`.
- **Rationale**: This creates a clear hierarchy where any moving vehicle is more important than a parked one.

### 2. ID-Based Arbitration Logic
- **Decision**: Change `should_i_yield = (my_prio == other_prio and self.id < other_id)` to `should_i_yield = (my_prio == other_prio and self.id > other_id)`.
- **Rationale**: In equal priority cases, the vehicle with the "higher" (larger) ID will yield. This is a common convention and ensures a deterministic outcome.

### 3. State-Based Yield Check
- **Decision**: Ensure `check_proactive_evasion` is called frequently enough to handle manual moves.
- **Rationale**: The existing 0.05s check interval is sufficient, but it relies on correctly calculated priorities.

## Risks / Trade-offs

- **[Risk] ID Jitter** ➔ ID strings are unique and stable, so arbitration is deterministic.
- **[Risk] Deadlock on Equal Priority** ➔ The tie-breaker ensures that one vehicle always has permission to move while the other yields.
