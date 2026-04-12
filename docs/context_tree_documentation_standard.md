# Whitepaper: Context Tree Documentation Standard (Adapted for Steeven's Workflow)

## Version: 1.0
**Date:** March 31, 2026  
**Author:** Steeven Andrian's AI Coder Assistant

### Abstract
This document outlines the standardized methodology for creating and maintaining project documentation within a hierarchical knowledge base, herein referred to as the "Context Tree".

### 3. Context Tree Structure
The documentation resides within the `./docs/context-tree/` directory of the project root. It follows a three-tiered hierarchy:

#### 3.1. Domains
- **Naming:** Singular, PascalCase, or clear snake_case (e.g., `Authentication`, `Skills`).

#### 3.2. Topics
- **Naming:** Descriptive, singular names (e.g., `Skills/Architecture`).

#### 3.3. Subtopics (Optional)
- **Naming:** Lower-case, descriptive names separated by hyphens.

### 4. File Standardization
Each node requires an overview file named `context.md`. Individual pieces of knowledge are stored in separate `.md` files.

#### 4.2. Knowledge Files
##### 4.2.1. YAML Frontmatter
```yaml
---
title: "Descriptive Title"
tags: ["tags"]
keywords: ["keywords"]
related: []
importance: 50
recency: 1.0
maturity: draft
accessCount: 0
updateCount: 1
createdAt: "2026-03-31T00:00:00Z"
updatedAt: "2026-03-31T00:00:00Z"
---
```
##### 4.2.2. Content Sections
- **Raw Concept (Optional)**
- **Narrative (Primary)**
- **Facts (Optional)**
