# Proposal: V6.0 Swarm Intelligence & Autonomous Yielding

## 1. Problem Statement
The current AGV fleet operates as isolated entities. When two AGVs encounter each other in a narrow corridor, they both stop due to safety protocols, resulting in a permanent deadlock. There is no mechanism for dynamic priority or cooperative behavior.

## 2. Proposed Change
Upgrade the fleet with "Social Intelligence" to enable decentralized decision-making and cooperative navigation.

### Key Features:
- **Collision Diagnosis**: Enhancing the controller to identify the specific cause of a block (Wall vs. AGV ID).
- **Dynamic Priority**: Implementing a scoring system that accounts for task status, progress, and waiting time.
- **Intersection-based Haven Search**: Developing a BFS-based escape planner to find safe intersections for yielding.
- **Social UI Feedback**: Updating the frontend to display AGV "thoughts" and relationship links between yielding/waiting pairs.

## 3. Impact & Benefits
- **Zero Deadlocks**: Resolves head-on conflicts in narrow corridors.
- **Increased Efficiency**: Higher priority tasks flow through bottlenecks faster.
- **Improved UX**: Users can see "why" an AGV is waiting and where it is "escaping" to.

## 4. Proposed Timeline
1. Backend Culprit Diagnosis & Status Machine Update.
2. BFS Escape Planner (Intersection Search) Implementation.
3. Dynamic Priority Arbitrator & Social UI Layer.
