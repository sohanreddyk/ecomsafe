# EcomSafe

**Cart Before the Harm: Real-Time Safety Detection in E-Commerce Conversational Agents**

> **Status: ongoing research, Phase 1: benchmark construction and validation.**
>
> | Phase | Status |
> |---|---|
> | Phase 1: benchmark construction and validation | Current |
> | Phase 2: single-turn detector / hidden-state probe evaluation | Planned |
> | Phase 3: multi-turn trajectory detection | Planned |
>
> No detection experiments have been run yet. No pilot dataset is the final EcomSafeBench.

## Team

### Student Researchers
- Sohan Jayram Reddy Kadiri — Northeastern University
- Sanidhya Khandelwal — Northeastern University
- Rohan Raj — Northeastern University

### Project Guides
- Jayash Koshal — Northeastern University
- Shanu Sushmita — Northeastern University

## Project Overview

EcomSafe studies safety for LLM-based shopping assistants. These agents operate under business constraints such as pricing logic, return policies, competitor rules and regulatory requirements. That exposes them to *commercial jailbreaks*: requests that try to make the assistant break a business rule, rather than produce conventionally harmful content.

Commercial jailbreaks talk about the same products, policies and topics as legitimate shopping requests. A useful benchmark must therefore not let a model spot attacks from topic words or obvious phrasing alone.

The project is staged:

1. **Phase 1 (current): benchmark construction and validation.**
   - Build a policy-grounded benchmark of single-turn commercial jailbreaks.
   - Pair every attack with a matched legitimate negative, and add legitimate boundary cases.
   - Validate the labels, and keep lexical shortcuts to a minimum.
2. **Phase 2 (planned): single-turn detection.** Evaluate lexical, contextual and representation-level (hidden-state probe) detectors on the validated benchmark, including held-out product domains, attack types and techniques.
3. **Phase 3 (planned): multi-turn trajectory detection.** Extend to multi-turn escalation.

**Original detector design (Phases 2–3, not implemented).** The proposal's detector has two parts:
- a per-turn probe over model hidden states that estimates commercial intent;
- an incremental trajectory layer over the per-turn risk scores. It uses four features: escalation-rate delta, running mean risk, risk volatility, and Kendall's rank correlation with turn index.

Trajectory-aware safety detection is prior work, and we do not claim it as new.

## Research Motivation

- **The harm is a business-rule violation.** A response can look harmless as text while still breaking a business rule, such as an unauthorized discount or guidance for a fraudulent return.
- **Attacks and legitimate requests share vocabulary.** A detector trained on unmatched data can learn topic or phrasing instead of intent. That is why Phase 1 pairs every attack with a matched negative and audits lexical separability.
- **False positives are costly.** Legitimate shopping traffic is the normal case, so over-blocking has a direct business cost. Boundary cases measure this.
- **Escalation can span turns.** Per-message filters can miss attacks spread across turns that each look benign. Phase 3 addresses this.

## Threat Taxonomy

Five commercial jailbreak types, as defined in the project proposal:

| Attack type | Attacker goal | Request intent label |
|---|---|---|
| Price manipulation | Override pricing logic or extract unearned discounts | PV |
| Policy bypass | Circumvent return, refund or warranty policies | PV |
| Return fraud | Get guidance for fraudulent returns | FF |
| Competitor extraction | Force unauthorized competitor comparisons or intelligence leaks | CD |
| Regulatory bypass | Get age-gated, prescription or restricted products or information | RB |

**Request intent labels:** PV (Policy Violation), CD (Competitive Disclosure), FF (Fraud Facilitation), RB (Regulatory Breach) and BENIGN.

**Response labels:** CR (Compliant Refusal) describes how a target model *responded*. It will be assigned only after target-model responses are collected, and it is not a shopper-intent label.

**Multi-turn escalation patterns (Phase 3):**
- **Linear:** risk rises steadily.
- **Camouflaged:** harmful turns are interleaved with benign ones.
- **Late spike:** a high-risk request follows several safe turns.

## EcomSafeBench: Planned, Implemented, and Observed

The full 3,900-conversation EcomSafeBench has not been constructed. The single-turn generation and validation pipeline is implemented and has produced small pilot datasets.

**A. Original proposal (planned).** 3,900 annotated conversations across five product domains: electronics, pharmaceuticals, fashion, financial products and groceries.

| Subset | Conversations |
|---|---|
| Commercial jailbreaks | 1,300 |
| Multi-turn escalation | 1,100 |
| Benign / control | 1,500 |

Planned evaluation:
- ROC AUC per threat class;
- early-detection rate (attacks caught before turn 5);
- false-positive rate on benign shopping dialogues;
- per-turn latency.

Results will be broken down by threat class and product domain.

**B. Implemented (`data_generation/`).** A single-turn generation and validation pipeline for Threat Class 1:
1. Taxonomy-driven planning that fixes labels before any text exists.
2. Prompts grounded in each domain's policy text.
3. Generation of attacks, matched negatives and boundary cases.
4. Rule and near-duplicate filters.
5. A blind judge from a different model family, with repair of rejected matched negatives.
6. Pair integrity checks.
7. Grouped and held-out splits.
8. A lexical shortcut audit.
9. Annotation and preflight tooling.

Multi-turn scaffolding is implemented but has not yet been run.

**C. Observed (pilot data).** The current headline pilot is `pilot_150`:
- 392 messages generated, 289 kept;
- 126 attacks, 126 matched negatives and 37 boundary cases;
- every record is one shopper message;
- train/val/test is 195/35/59.

A grouped 5-fold Naive Bayes audit on unigrams and bigrams separates attacks from matched negatives with 0.905 accuracy. Because the audit sees only surface wording, high accuracy is bad for dataset quality: substantial lexical shortcuts remain. This number is not detector performance.

See [`data_generation/README.md`](data_generation/README.md) for all runs and caveats.

## Repository Structure

```
EcomSafe/
├── README.md
├── requirements.txt         # Initial planned dependencies (versions to be pinned)
├── data_generation/         # EcomSafeBench generation and validation pipeline: code, configs, prompt templates, tests, pilot reports
├── src/                     # Scaffold: future detector code (Phase 2+)
├── configs/                 # Scaffold: future experiment configs
├── experiments/             # Scaffold: future experiment outputs
├── paper/
│   ├── acm/                 # Earlier ACM LaTeX draft
│   ├── submission_update1/  # Project Update 1 report (frozen)
│   └── *.md                 # Update 1 section drafts
└── literature_review/       # Literature notes and verified peer-reviewed cores (Update 1, Update 2)
```

`data_generation/` is the canonical EcomSafeBench generation and validation pipeline. See [`data_generation/README.md`](data_generation/README.md).

## Current Status

- **Done:**
  - Project Update 1: problem, related work, taxonomy, planned design.
  - Verified peer-reviewed literature cores (`literature_review/`).
  - The single-turn generation and validation pipeline (`data_generation/`), with seven pilot runs. `pilot_150` is the headline and `pilot_v5` is the iteration comparison.
- **Not yet done:**
  - human validation (tooling exists, no annotation has been run);
  - multi-turn generation;
  - any detector, probe, trajectory layer, baseline or experiment.

## Next Steps

Next cycle, in order:
1. **Human validation.** About 100 items, 2 independent annotators, with human-vs-human agreement added. Keep the human-vs-design and human-vs-judge Cohen's κ. Disagreements are resolved by discussion.
2. **Reduce lexical shortcuts.** Another iteration of matched-negative and attack phrasing.
3. **Address generator refusals.** They concentrate in return fraud and instruction injection.
4. **Freeze, then scale.** Freeze a validated single-turn version, then scale it.
5. **Phase 2 baselines, in parallel on frozen pilot data, as sanity checks only:**
   - lexical and sentence-embedding baselines;
   - hidden-state extraction with a linear probe;
   - held-out evaluation;
   - false positives on boundary cases.
6. **Later (Phase 3): multi-turn generation and trajectory features.** The "before turn 5" early-detection metric must first be reconciled with the configured 3–7 turn range.
