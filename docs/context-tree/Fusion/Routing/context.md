# Topic: Routing

## Overview
Fusion Routing (The Automatic Pipeline) is the dynamic decision-making layer that selects the most efficient thinking strategy for a given session. It monitors real-time scoring data to determine when to stick to a strategy or pivot to a more complex one.

## Key Concepts
- **Automatic Pipeline**: The logic that maps problem types to initial strategies.
- **Dynamic Pivoting**: The self-correcting mechanism that swaps engines mid-session based on low quality scores.
- **Pivot Thresholds**: Configurable scoring benchmarks (e.g. coherence < 0.6) that trigger a strategy change.

## Related Topics
- [Fusion Orchestration](../Orchestration/context.md)
- [Scoring Engine](../../Analysis/context.md)
