# Proposal: V6.0 Professional Workstation UI/UX Refactor

## 1. Problem Statement
The current UI is functional but lacks professional grade organization. Information about fleet management, individual AGV telemetry, and algorithm visualization are all mixed in a single sidebar, leading to visual clutter and potential misoperation. The canvas also lacks scalability for larger warehouse maps.

## 2. Proposed Change
Transform the simulator from a basic web app into a "Professional Workstation" architecture. This involves a layout overhaul, enhanced visual aesthetics, and advanced interaction modes.

### Key Objectives:
- **Dual-Wing Layout**: Split management and inspection into left and right panels.
- **Dark Mode**: Implement a high-contrast, dark-themed UI for long-term monitoring.
- **Tool-Based Interaction**: Separate building, selecting, and navigating into distinct modes.
- **Infinite Canvas**: Add Zoom and Pan capabilities to handle large-scale simulations.

## 3. Impact & Benefits
- **Operational Safety**: Mode-based tools prevent accidental obstacle creation while setting targets.
- **Scalability**: Support for 50m+ maps with fine detail observation.
- **Professionalism**: Dark mode and data visualization (sparklines) increase the simulator's industrial credibility.
- **User Comfort**: Reduced eye strain and more intuitive "left-select, right-inspect" workflow.

## 4. Proposed Timeline
1. CSS Foundation & Dark Mode.
2. Layout Refactoring (Dual Sidebar).
3. Tool Mode Implementation.
4. Canvas Matrix Transformation (Zoom/Pan).
