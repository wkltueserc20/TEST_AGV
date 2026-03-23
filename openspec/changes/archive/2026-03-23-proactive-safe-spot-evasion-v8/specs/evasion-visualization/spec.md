## ADDED Requirements

### Requirement: Evasion target visualization
The system MUST render visual markers at the current evasion target of any AGV in the EVADING state.

#### Scenario: Dashed marker at target
- **WHEN** an AGV's status is EVADING
- **THEN** the frontend SHALL render a dashed purple circle at its `evasion_target` coordinates.
