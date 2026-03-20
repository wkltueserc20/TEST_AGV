## ADDED Requirements

### Requirement: Conflict-aware proactive evasion
Idle AGVs MUST proactively detect potential collisions with projected paths of other vehicles and move to clear the way.

#### Scenario: Proactive yield
- **WHEN** an IDLE AGV's current position is within 1200mm of any point in the `path_occupancy` map
- **THEN** it SHALL transition to EVADING state and move to the nearest safe Haven.
