## ADDED Requirements

### Requirement: Real-time path projection
The system MUST allow moving AGVs to project their intended future path segments (up to 3000mm) into a shared World occupancy map.

#### Scenario: Occupancy update
- **WHEN** an AGV is in EXECUTING or EVADING state
- **THEN** it SHALL update its entry in the World's `path_occupancy` registry at 20Hz.
