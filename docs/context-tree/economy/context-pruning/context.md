# Topic: Context Pruning

## Overview
Context Pruning is the mechanism used to manage the density of the session history. As cognitive sessions grow in depth and branching complexity, the system must selectively filter the "Active Context" to prevent token overflow and focus the attention of the LLM on relevant reasoning paths.

## Key Concepts
- **Ancestral Filtering**: Isolating the direct logical path of a solution.
- **Dynamic Summarization**: Swapping high-token raw content for low-token summaries in distant history.
- **Strategy Pivoting**: The ability to switch pruning methods based on the current depth or session profile.

## Related Topics
- [Pruning Strategies](pruning-strategies.md)
- [../context.md](../context.md)
