# Domain: Fusion

## Purpose
The Fusion domain is responsible for the convergent phase of the cognitive process. It focuses on synthesizing multiple, often divergent, information paths or expert perspectives into high-density, high-quality unified conclusions.

## Scope
Included in this domain:
- **Convergent Synthesis**: Logic to merge multiple `EnhancedThought` nodes into a single synthesis node.
- **Cognitive Routing**: The 'Automatic Pipeline' logic that dynamically selects and pivots thinking strategies.
- **Convergence Analysis**: Determining when a reasoning path has reached a sufficient level of coherence to conclude.

Excluded from this domain:
- **Divergent Generation**: The creation of initial options (handled by individual primitive engines).
- **Persistent Storage**: Handled by the `Memory` domain.
- **Scoring Algorithms**: Handled by the `Analysis` domain (though Fusion heavily consumes these metrics).

## Usage
Developers should reference this domain when:
- Implementing new hybrid modes that require a 'consensus' or 'fusion' step.
- Fine-tuning the 'Automatic Pipeline' routing weights and thresholds.
- Adding new synthesis heuristics or LLM synthesis prompts.
- Troubleshooting session pivots or early termination logic.

## Key Concepts
- [Convergent Synthesis](file:///c:/Users/steevenz/MCP/mcp-cct-server/docs/context-tree/Fusion/Orchestration/context.md)
- [Dynamic Routing](file:///c:/Users/steevenz/MCP/mcp-cct-server/docs/context-tree/Fusion/Routing/context.md)
