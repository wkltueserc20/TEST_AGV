## ADDED Requirements

### Requirement: State-Based Priority Levels
The AGV system SHALL assign priority levels based on the current execution status and task assignment. 
- Critical tasks (loading/unloading/near destination source) MUST have highest priority (0-4).
- Active tasks MUST have priority 5.
- Moving or planning states (even without a task) MUST have priority 50.
- Idle states MUST have lowest priority 100.

#### Scenario: Idle vehicle yielding to moving vehicle
- **WHEN** AGV-A is `IDLE` and AGV-B is `EXECUTING` (moving in SINGLE mode)
- **THEN** AGV-A SHALL have a lower priority (numerical value 100) than AGV-B (numerical value 50)
- **THEN** AGV-A SHALL yield and proactively evade AGV-B if a conflict is detected.

### Requirement: Consistent Conflict Arbitration
When two AGVs have equal priority and a path conflict occurs, the system SHALL use a deterministic ID-based arbitration rule.

#### Scenario: Equal priority arbitration
- **WHEN** AGV-A and AGV-B both have priority 50
- **WHEN** AGV-A has ID "AGV-1" and AGV-B has ID "AGV-2"
- **THEN** the AGV with the larger ID ("AGV-2") SHALL be considered lower priority and yield to the AGV with the smaller ID ("AGV-1").

### Requirement: Proactive Evasion for Manual Moves
The proactive evasion mechanism SHALL monitor conflicts even when an AGV is being manually controlled in SINGLE mode (i.e., has no `current_task` but is `is_running`).

#### Scenario: Conflict detected during manual move
- **WHEN** an AGV is moving without a task (SINGLE mode)
- **WHEN** a conflict is detected with a higher-priority vehicle
- **THEN** the AGV SHALL trigger an evasion maneuver to a safe spot.
