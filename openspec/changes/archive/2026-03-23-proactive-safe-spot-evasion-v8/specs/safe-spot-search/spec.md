## ADDED Requirements

### Requirement: BFS-based safe spot discovery
The system MUST provide a BFS algorithm to find the nearest grid cell that is both physically safe and free from projected path conflicts.

#### Scenario: Find closest unoccupied cell
- **WHEN** an AGV is conflicted with another path
- **THEN** the system SHALL return the nearest (X, Y) coordinate that fits the 1000x1000mm footprint and is not in the threat grid.
