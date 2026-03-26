## ADDED Requirements

### Requirement: Search Debug Telemetry State Independence
The backend system SHALL include the `visited` nodes (search debug data) in the telemetry payload regardless of whether the AGV is currently in the `is_running` state.

#### Scenario: Telemetry during movement
- **WHEN** an AGV is moving along a path (`is_running` is true)
- **THEN** the telemetry `visited` field MUST contain the search nodes from the most recent path planning operation.

### Requirement: Telemetry Payload Optimization
The backend SHALL optimize the `visited` nodes list before transmission by applying sparse sampling (taking every 5th node) and capping the total number of nodes to 1000.

#### Scenario: Large search space optimization
- **WHEN** an A* search visits 10,000 nodes
- **THEN** the telemetry payload SHALL contain exactly 1000 nodes (sampled from every 10th node in this case, or the first 5000 sampled at every 5th). *Correction*: Taking every 5th and capping at 1000 means only the first 5000 original nodes are represented if we cap at the end. Or better: take every `max(1, len(nodes)//1000)`? No, let's stick to simple: every 5th, then cap.

#### Scenario: Small search space integrity
- **WHEN** an A* search visits 100 nodes
- **THEN** the telemetry payload SHALL contain 20 nodes (every 5th node).

### Requirement: Frontend Animation Trigger
The frontend SHALL detect changes in the `visited` nodes via the fingerprinting mechanism and trigger the progressive revealing animation immediately upon receipt, regardless of AGV motion.

#### Scenario: Animation start during movement
- **WHEN** the frontend receives a new `visited` array with a different fingerprint while the AGV is moving
- **THEN** the Search Debug Layer MUST begin its progressive revealing animation (revealing 100 nodes per frame).
