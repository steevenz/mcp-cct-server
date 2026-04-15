# Domain: Finance

## Purpose
The Finance domain handles all aspects of **Cognitive Investment Tracking**. It ensures that every cognitive operation (token usage) is audited, priced, and converted into human-understandable financial metrics (USD/IDR).

## Scope
Included in this domain:
- **Pricing Management**: Loading and fuzzy-matching model pricing datasets.
- **Cost Calculation**: High-precision arithmetic for token-to-currency conversion.
- **Forex Service**: Dynamic currency exchange rate retrieval (USD -> IDR).
- **Cost Averaging**: Pessimistic fallback logic for unknown models.

Excluded from this domain:
- Core LLM inference logic (handled by `Infrastructure`).
- Memory persistence of session history (handled by `Memory`).

## Usage
Reference this domain when updating pricing datasets, modifying the forex update frequency, or enhancing the "Pessimistic" fallback threshold.

---

# Topic: CostAveraging

## Overview
The Cost Averaging system provides a safety net for financial transparency. In the volatile landscape of AI models, exact pricing is not always available at launch.

## Key Concepts
- **ai-common-model**: A virtual model representing the average cost of "Premium" flagship models.
- **Pessimistic Threshold**: We prioritize safety by taking the highest average of premium tiers (Pro, Opus, Ultra) to prevent billing under-reporting.

## Related Topics
- [PricingManager](../../src/utils/pricing.py) - Implementation of the calculation logic.
- [Datasets](../../database/datasets/) - Raw pricing source of truth.
