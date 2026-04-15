# Topic: Transport Modes

## Overview
The CCT server follows the Model Context Protocol (MCP) standards for communication. It supports two primary transport modes, allowing it to function as a local IDE companion or a remote cognitive service. 

## Key Concepts
- **STDIO Transport**: The default and most stable mode for local development. It uses the standard input/output streams of the process for JSON-RPC communication.
- **HTTP Transport**: Enables communication over a network, making the CCT server accessible as a web service.
- **Bootstrapping Lifecycle**: The deterministic 7-step process the server follows to initialize its core cognitive engines before accepting requests.

## Related Topics
- [../environment_variables.md](../environment-variables.md)
- [../context.md](../context.md)

## Narrative: The Bootstrapping Sequence
When `main.py` is executed, the server undergoes a structured "Cognitive Birth" sequence to ensure all **Critical** pillars are locked before **Creative** work begins:
1. **Config Load**: Environment variables are locked into immutable settings.
2. **Memory Init**: The SQLite managers establish WAL-mode connections and serialization locks.
3. **Engine Init**: The Sequential and Scoring engines are provisioned.
4. **Service Init**: Fusion and Automatic Routing services are established.
5. **Strategy Registry**: All 22+ primitive and hybrid strategies are loaded and mapped into the central registry.
6. **Orchestrator Facade**: The `CognitiveOrchestrator` is created to unify access to the registry and engines.
7. **Tool Registration**: The MCP tool boundaries are exposed to the transport layer.

## Facts
- **fastmcp_powered**: The server leverages the `FastMCP` wrapper to handle the complexities of the JSON-RPC protocol across both transport modes. [bridge]
- **stdio_priority**: For production IDE deployments (e.g., Trae), STDIO remains the strongly recommended transport due to its low latency and zero-config socket management. [best-practice]
- **graceful_shutdown**: The entry point handles `KeyboardInterrupt` and fatal exceptions to ensure that the memory layer closes all database handles cleanly. [stability]
