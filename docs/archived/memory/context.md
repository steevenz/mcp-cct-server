---
title: "Domain: Memory"
tags: ["core", "persistence", "sqlite", "c&c"]
keywords: ["memory", "archival", "wal", "audit", "pattern"]
importance: 90
recency: 1.0
maturity: "validated"
createdAt: "2026-04-12T18:00:00Z"
updatedAt: "2026-04-12T18:00:00Z"
---

# Domain: Memory

## Purpose
The Memory domain handles the long-term persistence and retrieval of cognitive states. It ensures that every thread of reasoning is archived, allowing for session recovery, cross-session pattern matching, and long-term cognitive growth.

## Scope
Included in this domain:
- **Persistence Logic**: `MemoryManager` using SQLite with Write-Ahead Logging (WAL) for concurrency.
- **Document Store Pattern**: Storing complex Pydantic models as optimized JSON blobs for flexibility.
- **Security & Multi-tenancy**: Session ownership validation via cryptographically random bearer tokens and path traversal hardening.
- **Audit Trails**: Structured forensic logging of every write operation (SECURITY M2).
- **Cognitive Archiving**: Automated saving of "Golden Thinking Patterns" and cognitive "Anti-Patterns" (Mental Immune System).

Excluded from this domain:
- **In-memory cache**: Transient execution state handled within specific engine blocks.
- **Static Assets**: Configuration files (handled in `Core`).

## Usage
Developers should reference this domain when:
- Adding new tables or indexes to the cognitive database.
- Modifying how session history is retrieved or pruned.
- Implementing new persistence formats or hardening against concurrent write collisions.

## C&C Framework Alignment
The Memory domain acts as the **Critical** archive. By documenting every failure (`AntiPattern`) and success (`GoldenPattern`), it provides the fundamental feedback loop. It transitions the system from "one-off" creative thoughts to "battle-tested" critical frameworks.
