## Why

The Search Debug Layer (showing visited nodes during A* planning) is currently hidden when the AGV is moving, causing a delay where the visualization only appears after the AGV has reached its destination. This prevents users from seeing the path planning process in real-time, which is critical for debugging and understanding the system's decision-making.

## What Changes

- **Telemetry Data Expansion**: Modify `backend/agv.py` to always include `visited_nodes` in the telemetry data, removing the current restriction that hides this data while `is_running` is true.
- **Bandwidth Optimization**: Implement sparse sampling (e.g., every 5th node) or a hard limit (e.g., top 1000 nodes) on the `visited_nodes` sent to the frontend to prevent performance degradation due to large JSON payloads.
- **UI Synchronization**: Ensure the frontend receives and begins the "revealing" animation for the search debug layer as soon as the path is computed, allowing the visualization to play out while the AGV is in transit.

## Capabilities

### New Capabilities
- `search-debug-synchronization`: Real-time synchronization of path planning search nodes with AGV movement and path rendering.

### Modified Capabilities
- None

## Impact

- **Backend**: `backend/agv.py` (`to_dict` method), `backend/main.py` (telemetry broadcast frequency/size).
- **Frontend**: `frontend/src/SimulatorCanvas.tsx` (timing of search layer activation).
- **Network**: Increased WebSocket payload size per telemetry update (managed via sampling).
