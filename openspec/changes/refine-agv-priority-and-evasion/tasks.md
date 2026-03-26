## 1. Backend Priority Logic Refinement

- [x] 1.1 Update `get_priority` in `backend/agv.py` to incorporate `status` (IDLE/EXECUTING/PLANNING) into priority calculation.
- [x] 1.2 Modify `check_proactive_evasion` in `backend/agv.py` to change the tie-breaker rule to `self.id > other_id`.

## 2. Validation & Testing

- [x] 2.1 Test Case: Two AGVs in SINGLE mode moving towards each other. Verify the larger ID vehicle yields.
- [x] 2.2 Test Case: Idle large-ID AGV in the path of a moving small-ID AGV. Verify the idle AGV proactively evades.
- [x] 2.3 Verify automated mission priority (AUTO mode) still overrides manual move priority correctly.
