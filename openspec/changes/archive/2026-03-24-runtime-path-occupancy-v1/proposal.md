# Proposal: Run-time Path Occupancy Publishing

## Summary
Change the timing of path occupancy (repulsion zone) publishing to occur only when an AGV is in the `is_running` state. This prevents AGVs from triggering proactive evasion in other robots while the user is merely testing or previewing paths.

## Background
Currently, any AGV with a `global_path` publishes its occupancy to the world. Other AGVs detect this and trigger evasion immediately, even if the source AGV has not started its mission (Start button not clicked). This leads to unnecessary movements and confusion during route setup.

## Goals
- Only publish path occupancy when `is_running` is True.
- Immediately clear path occupancy when `is_running` becomes False.
- Ensure visual feedback (red circles) matches the active threat level.

## Success Criteria
1. Setting a target for AGV-A shows the red dashed path line, but AGV-B stays still.
2. Clicking START on AGV-A causes the red occupancy circles to appear, and AGV-B moves away if in conflict.
3. Pausing or completing the mission on AGV-A clears the red circles and stops the threat to others.
