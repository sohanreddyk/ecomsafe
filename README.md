# EcomSafe

**Cart Before the Harm: Real-Time Safety Detection in E-Commerce Conversational Agents**

> **Status: ongoing research.** No experimental results have been produced yet. This repository currently contains the project report and literature review. Code and data will be added in upcoming project cycles.

## Team

### Student Researchers
- Sohan Jayram Reddy Kadiri — Northeastern University
- Sanidhya Khandelwal — Northeastern University
- Rohan Raj — Northeastern University

### Project Guides
- Jayash Koshal — Northeastern University
- Shanu Sushmita — Northeastern University

## Project Overview

EcomSafe studies safety detection for LLM-based shopping assistants. Unlike general-purpose chatbots, these agents operate under business constraints such as pricing logic, brand rules, return policies, and regulatory guidelines. That exposes them to *commercial jailbreaks*: adversarial requests that target business rules rather than conventionally harmful content.

EcomSafe proposes a two-layer, trajectory-aware detector. A per-turn probe over model hidden states estimates commercial intent. An incremental trajectory layer then summarizes risk across the conversation using four features:
- escalation rate delta;
- running mean risk;
- risk volatility;
- Kendall's rank correlation with turn index.

Trajectory-aware safety detection already exists in prior work, so we do not claim it as new. Our research question is narrower: does trajectory-aware detection over a hidden-state intent probe help detect commercial jailbreaks early across e-commerce product domains?

## Research Motivation

- **Guard filters judge messages one at a time.** Guard classifiers that judge each message in isolation can miss attacks spread across several turns that each look benign.
- **The harm is a business-rule violation.** In commerce, the output may look harmless as text while still violating a business rule, for example an unauthorized discount or guidance for a fraudulent return.
- **False positives are costly.** Benign shopping dialogues are the normal case, so over-blocking has a direct business cost.

## Threat Taxonomy

We use five commercial jailbreak types, as defined in the project proposal:

| Attack type | Attacker goal |
|---|---|
| Price manipulation | Override pricing logic or extract unearned discounts |
| Policy bypass | Circumvent return, refund, or warranty policies |
| Return fraud | Get step-by-step guidance for fraudulent returns |
| Competitor extraction | Force unauthorized competitor comparison or intelligence leaks |
| Regulatory bypass | Extract age-gated, prescription, or restricted product information |

Multi-turn escalation patterns:
- **Linear:** risk increases steadily each turn.
- **Camouflaged:** harmful prompts are interleaved with benign turns.
- **Late spike:** a high-risk request arrives after several safe turns.

## Planned EcomSafeBench

EcomSafeBench is a **planned** benchmark and has not been built yet. The planned design has 3,900 annotated conversations across five product domains: electronics, pharmaceuticals, fashion, financial products, and groceries.

| Subset | Conversations |
|---|---|
| Commercial jailbreaks | 1,300 |
| Multi-turn escalation | 1,100 |
| Control / benign | 1,500 |

Planned evaluation:
- **Metrics:** ROC AUC per threat class, early-detection rate (attacks caught before turn 5), false-positive rate on benign shopping dialogues, and per-turn latency.
- **Analysis:** results are broken down by threat class and product domain.
- **Baselines:** per-turn classifiers, output and keyword filters, sliding-window max-risk, and full-context models.

## Repository Structure

```
EcomSafe/
├── README.md
├── requirements.txt         # Initial planned dependencies (versions to be pinned)
├── src/                     # Scaffold: future probe, trajectory layer, baselines, evaluation
├── configs/                 # Scaffold: future reproducible experiment configs
├── data/                    # Scaffold: future EcomSafeBench pilot and benchmark data
├── experiments/             # Scaffold: future pilot outputs and logs
├── paper/
│   ├── acm/                 # Earlier ACM LaTeX draft
│   ├── submission_update1/  # Project Update 1 submission report
│   └── *.md                 # Report section drafts
├── literature_review/       # Literature notes, verified peer-reviewed core, gap analysis
└── papers/                  # Source PDFs used for the literature review
```

The repository is currently in the research and planning stage. The `src/`, `configs/`, `data/`, and `experiments/` directories contain only scaffold README files; implementation begins in the next cycle.

## Current Status

- **Done:** the project report, covering the problem description, related work, threat taxonomy, dataset design, and plan.
- **Done:** a literature review with a verified peer-reviewed core.
- **Not yet started:** code, the benchmark data, and experiments.

## Next Steps

The next two-week cycle builds an end-to-end **pilot**:
1. Set up the repository, a pinned environment, and reproducible configuration.
2. Encode the threat taxonomy and annotation schema.
3. Build a pilot of about 150 conversations (50 commercial jailbreaks, 40 escalations, 60 benign) across all five domains, with manual review.
4. Implement the baselines: per-turn classifier, keyword and output filter, sliding-window max-risk, and full-context.
5. Build a hidden-state extraction script and a linear intent probe (PV/CD/FF/RB/CR) on Llama-3.2-3B-Instruct.
6. Implement the trajectory features and a simple sequence model.
7. Compute all four metrics on held-out pilot conversations as sanity checks, not reportable results.

The Project Update 1 report is in `paper/submission_update1/main.tex`.
