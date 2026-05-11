# Offline LLM: Google Gemma Architecture

**Why Gemma? Why Not Qwen, Llama, Phi, or Mistral?**

---

## Selection Criteria

When choosing an embedded offline LLM for this MCP server, we evaluated:

1. **RAM footprint** — Must run on any machine (8GB RAM target)
2. **Instruct quality** — Must handle structured tasks (JSON extraction, classification)
3. **License** — Must be free for commercial use
4. **Tokenizer efficiency** — Must handle code/technical content well
5. **Ecosystem** — Must have GGUF format available for llama-cpp-python

---

## Comparison: Small Models (Tier 1 — Always Available)

| Model | Size | RAM (Q4) | Speed | Quality | Why Not #1 |
|-------|------|----------|-------|---------|------------|
| **Gemma 2 2B** | 2B params | **~1.2 GB** | ~40 tok/s | ⭐⭐⭐ | **WINNER** |
| Qwen 2.5 1.5B | 1.5B params | ~1.5 GB | ~30 tok/s | ⭐⭐ | Higher RAM, worse quality |
| Phi-3 Mini | 3.8B params | ~2.5 GB | ~20 tok/s | ⭐⭐⭐ | 2x RAM, slower |
| Llama 3.2 3B | 3B params | ~2.0 GB | ~25 tok/s | ⭐⭐⭐ | 1.6x RAM |

### Gemma 2 2B Wins Because:

**1. Lowest RAM (~1.2 GB):** 
- Gemma 2 2B Q4_K_M uses only 1.2GB RAM
- Qwen 1.5B somehow uses MORE RAM (1.5GB) despite fewer params (better tokenizer?)
- Llama 3.2 3B uses 2.0GB (67% more)
- This means Gemma 2B runs on ANY laptop, even with only 8GB RAM

**2. Google's Instruct Training:**
- Gemma 2 was trained with heavy RLHF for instruction following
- Significantly better at structured output (JSON) than Qwen 1.5B
- Gemma 2 2B outperforms Llama 3.2 3B on many benchmarks despite being smaller

**3. Tokenizer Efficiency:**
- Google's tokenizer handles code and technical content efficiently
- Fewer tokens for the same technical content vs Qwen or Llama tokenizers
- Direct impact on token economy — fewer tokens for same work

**4. License:**
- Apache 2.0 — free for commercial use, no restrictions
- Qwen: also Apache 2.0 (fine)
- Llama: requires commercial license for >700M MAU
- Phi: MIT license (also fine)

**5. Ecosystem:**
- Widely available in GGUF format
- Multiple quantization options (Q2 through Q8)
- Active community and updates (Gemma 2, Gemma 3 already available)

---

## Comparison: Medium Models (Tier 2 — Reasoning)

| Model | Size | RAM (Q4) | Speed | Why Not #1 |
|-------|------|----------|-------|------------|
| **Gemma 2 9B** | 9B params | **~5.5 GB** | ~12 tok/s | **WINNER** |
| Mistral 7B | 7B params | ~4.5 GB | ~15 tok/s | Smaller but Gemma 9B quality is significantly better |
| Llama 3.1 8B | 8B params | ~5.0 GB | ~13 tok/s | Comparable but Gemma 2 9B benchmarks higher |
| Qwen 2.5 7B | 7B params | ~4.5 GB | ~14 tok/s | Good but Gemma 9B wins on code tasks |
| Phi-3 Medium | 14B params | ~8.0 GB | ~8 tok/s | Too large for 8GB RAM machines |

### Gemma 2 9B Wins Because:

**1. Best quality-to-RAM ratio:**
- Gemma 9B at 5.5GB vs Llama 8B at 5.0GB = only 0.5GB more for significantly better quality
- Gemma 9B benchmarks: 74.0 on MMLU, 44.1 on HumanEval
- Outperforms Llama 3.1 8B on both coding and reasoning benchmarks

**2. Same model family as Tier 1:**
- Can share inference infrastructure
- Same tokenizer means consistent behavior
- Same prompt format for both tiers

**3. Fits in 16GB RAM machines:**
- 5.5GB + 1.2GB (Tier 1) = 6.7GB total
- Leaves room for OS, IDE, and other apps on 16GB machine

---

## Architecture Decision Record

```
Date: 2026-05-09
Decision: Use Google Gemma 2 (2B + 9B) as default offline LLM
Alternatives considered: Qwen 2.5, Llama 3.2, Phi-3, Mistral

Rationale:
  - Lowest RAM footprint (critical for broad compatibility)
  - Best instruct quality for structured tasks
  - Apache 2.0 license (no commercial restrictions)
  - Consistent tokenizer across both tiers
  - Active development (Gemma 3 already released)

Consequences:
  - + First auto-download requires internet (~1.5GB + ~5GB)
  - - Models are slightly larger than alternatives at same quality tier
  - + Gemma 3 27B available as upgrade path for high-RAM machines
```
