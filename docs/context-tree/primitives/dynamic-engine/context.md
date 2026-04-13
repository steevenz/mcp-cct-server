# Topic: Dynamic Engine

## Overview
The Dynamic Engine is the polymorphic execution core of the Primitives domain. Instead of having separate classes for every thinking strategy (e.g., `SearchEngine`, `AnalysisEngine`), the CCT server uses a single, high-performance factory that can dynamically adapt its logic based on the requested strategy type.

## Key Concepts
- **Unified Factory Pattern**: One engine class (`DynamicPrimitiveEngine`) handles all 22+ primitive strategies.
- **Contract Enforcement**: Inherits from `BaseCognitiveEngine` to ensure consistent memory and sequential engine access.
- **Embedded Scoring**: Every primitive step is automatically scored for quality and bias in real-time.

## Related Topics
- [Dynamic Factory Pattern](factory-pattern.md)
- [../context.md](../context.md)
