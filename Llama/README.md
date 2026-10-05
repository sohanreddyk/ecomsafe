# EcomSafeBench pilot batch 1: Llama pipeline

Everything in this folder was produced end to end by a local **Llama-3.2-3B-Instruct** model (fp16, Apple MPS), working from the ABCD dataset:

1. the agent policy;
2. the 25-cell test design;
3. 50 attack and 25 benign customer messages;
4. reference responses;
5. a self-audit.

`scripts/llama_scratch.py` runs the phases and applies automatic checks.

## Contents

| Path | What it is |
|---|---|
| `policy/ecomsafe_policy_llama.md` | Agent policy: 158 clauses. 131 are paraphrased from ABCD procedures, 9 come from ABCD action sequences, and 18 are new, covering pharmaceuticals, groceries, and financial products. |
| `policy/policy_llama.json` | The same policy in machine-readable form. It also lists clauses dropped as duplicates or for failing checks. |
| `policy/ABCD_DATA_USE_NOTICE.md` | ABCD licence (MIT), attribution, citation, and terms of use. |
| `data/batch1_design.json`, `data/batch1_design_matrix.md` | The 25-cell grid (5 attack types × 5 product domains): target clauses, cell strength, products, persuasion moves, and scenarios. |
| `data/batch1_records.jsonl` | **The batch:** 50 attack records and 25 benign minimal-pair companions. |
| `data/batch1_validation.md`, `data/batch1_validation_metrics.json` | Validation report and its raw numbers. |
| `data/batch1_verdict.md`, `data/batch1_self_audit.md` | Verdict, model self-audit, and manual review. All three are included in the validation report. |
| `data/generation_messages.json`, `data/batch1_src.json`, `data/batch1_self_audit_llama.json` | Intermediate outputs from each phase. |
| `data/pipeline_stats.json` | Model calls, attempts, and failures for each phase. |

## Pipeline

```
ABCD guidelines / ontology / KB
  │ policy     one call per ABCD procedure: extract enforceable rules in the model's own words
  │            + action-ordering rules + rules for pharmaceuticals, groceries, financial products
  │            → near-duplicates removed (embedding cosine ≥ 0.90), verbatim copies rejected
  ▼
policy (158 clauses)
  │ design     one call per cell; the model chooses from a shortlist of that cell's relevant clauses
  ▼
design (25 cells)
  │ generate   one call per attack + benign pair, under a randomly drawn register plan
  │ refs       violation predicate + correct refusal / response for every record
  │ selfaudit  the model judges whether each attack attacks and each benign record is honest
  │ build      records assembled with IDs, labels, clause text, metadata
  ▼
data/batch1_records.jsonl → scripts/validate_batch1.py → data/batch1_validation.md
```

**Automatic checks:**
- Each output is checked for valid JSON, refusals, stated intent to cheat, register match (casing, question vs request, length), and near-identical pairs. Failed outputs are retried, and the retry names the failed check.
- **Safety and brand checks are hard limits.** An output with dose or medical content, or a real brand name, is never kept, however many retries it takes.
- Product names and design scenarios are cleaned of real brand names, model numbers, and medicine strengths (`sanitize_product`, `scrub_text` in `scripts/llama_common.py`).
- Results are cached for each call, so an interrupted run resumes where it stopped.
- Running the pipeline writes every model attempt to `Llama/logs/` and a cache to `Llama/cache/`. Neither is committed: the raw attempts include outputs the checks rejected.

## Reproduce

Run from the repository root. This needs access to the gated `meta-llama/Llama-3.2-3B-Instruct` model on Hugging Face (`.venv/bin/hf auth login`). Expect roughly 1.5–2 hours on an Apple M4.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python scripts/llama_scratch.py all
```

```bash
.venv/bin/python scripts/validate_batch1.py && .venv/bin/python scripts/check_policy.py
```

To regenerate from scratch rather than from the cache, delete `Llama/cache/` first. Sampling is seeded per call, but GPU kernels on MPS are not guaranteed to be bit-for-bit deterministic.

## Data source

The policy is derived from ABCD: Chen et al., *Action-Based Conversations Dataset*, NAACL 2021, MIT licence, © 2021 ASAPP Research. See `policy/ABCD_DATA_USE_NOTICE.md`. ABCD's conversation file is not included in this repository.
