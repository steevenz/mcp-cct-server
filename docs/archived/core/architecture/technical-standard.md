---
title: "Standard: Context Tree Documentation (v5.0)"
tags: ["standard", "documentation", "kebab-case", "v5.0"]
keywords: ["rules", "naming", "frontmatter", "markdown"]
importance: 100
recency: 1.0
maturity: "core"
createdAt: "2026-04-13T00:00:00Z"
updatedAt: "2026-04-13T00:00:00Z"
---

# Context Tree Documentation Standard

## 1. Naming Convention (Absolute Rule)

All file and directory names MUST be **lowercase kebab-case**. 

*   **Directories**: `analysis`, `thinking-patterns`, `core-models`.
*   **Files**: `context.md`, `mission-standard.md`, `sqlite-schema.md`.
*   **Exception**: Root `README.md` and `docs/README.md` retain Uppercase for prominence.

## 2. Structure Layering

Documentation follows a hierarchical domain-topic structure:
`docs/context-tree/{domain}/{topic}/{file}.md`

## 3. Mandatory Frontmatter

Every documentation file MUST start with YAML frontmatter to facilitate AI search and ranking:

```yaml
---
title: "Human Readable Title"
tags: ["list", "of", "tags"]
keywords: ["search", "keywords"]
importance: 50 # 0-100
recency: 1.0 # 0.0-1.0
maturity: "draft" # draft, validated, core
createdAt: "YYYY-MM-DDTHH:MM:SSZ"
updatedAt: "YYYY-MM-DDTHH:MM:SSZ"
---
```

## 4. Section Structure (Narrative Clarity)

To ensure the "Lego Principle" and clean architecture:

1.  **Overview**: High-level "what and why".
2.  **Structures/Diagrams**: Mermaid.js workflow or structural maps.
3.  **Narrative**: Deep-dive explanation (Laravel Style).
4.  **Facts/Rules**: Bulleted list of absolute constraints.
5.  **Related Topics**: Relative path links to related documentation.

## 5. Metadata Scoring
- **Importance**: High-level arch docs = 100, specific helper docs = 50.
- **Maturity**: Anything synced with production code = `core`.

## Related Topics
- [../context.md](../context.md)
- [./context.md](./context.md)
