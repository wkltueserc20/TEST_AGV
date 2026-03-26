## Context

Currently, `AGV.to_dict()` in `backend/agv.py` suppresses the `visited` list if `self.is_running` is true. This prevents the frontend from receiving the A* search nodes (the "Search Debug Layer") while the AGV is in transit. The user only sees the result after the AGV stops, which feels like a lag or a bug in the visualization system.

## Goals / Non-Goals

**Goals:**
- Enable real-time visualization of A* search nodes as soon as a path is calculated.
- Maintain efficient telemetry transmission by managing the size of the `visited` list.
- Ensure the Search Debug Layer (blue nodes) and Path (red line) are logically synchronized in the UI.

**Non-Goals:**
- Modifying the A* search algorithm itself.
- Changing the frontend's progressive revealing animation (we only change when it starts).
- Implementing a delta-based telemetry system for search nodes.

## Decisions

### 1. Unified Telemetry for `visited_nodes`
- **Decision**: Remove the conditional check `if not self.is_running` in `backend/agv.py`.
- **Rationale**: The path (`global_path`) is already sent regardless of movement. The search nodes should follow the same logic to provide a complete picture of the "thinking" process.

### 2. Data Optimization (Sampling & Capping)
- **Decision**: Implement sparse sampling and a hard cap on the `visited` nodes array.
- **Sampling**: Take every 5th node from the `visited_nodes` list.
- **Capping**: Cap the resulting list at 1000 nodes.
- **Rationale**: 
    - A* can visit 10,000+ nodes. Sending all of them in every telemetry frame is inefficient.
    - 1000 sampled nodes (every 5th) effectively covers 5000 explored nodes, which is more than enough to visualize the search area around the AGV.
    - 1000 pairs of integers in JSON is approximately 12-16KB, a safe size for frequent WebSocket updates.

### 3. Synchronization Strategy
- **Decision**: Rely on the existing frontend "fingerprinting" logic.
- **Rationale**: `SimulatorCanvas.tsx` already uses a fingerprint (length and first node) to detect when a new search has occurred and resets the `revealedIndices` counter. By sending the data as soon as `is_planning` completes, the frontend will automatically trigger the animation while the AGV starts moving.

## Risks / Trade-offs

- **[Risk] WebSocket Congestion**: Multiple AGVs replanning simultaneously could spike the outgoing message size. 
  - **[Mitigation]**: The 1000-node cap ensures that even with 10 AGVs, the total overhead remains within manageable limits (<200KB per broadcast).
- **[Risk] Rendering Performance**: Rendering 1000 rectangles on a Canvas might be heavy for low-end devices.
  - **[Mitigation]**: The frontend already renders them progressively (100 per frame). Sampling ensures the total number of items the Canvas has to manage stays low.
