# EcomSafeBench Data Generation

`ecomsafe_datagen` is the **canonical dataset-generation pipeline** for EcomSafeBench.

## Current Status

- **Phase:** Phase 1 of the project, benchmark construction and validation.
- **Implemented:** Threat Class 1, single-turn commercial jailbreaks.
- **Multi-turn:** scaffolding is implemented but has not yet been run.
- **Not implemented:** no detector, hidden-state probe or trajectory layer exists. Those belong to Phases 2–3.
- **Pilots only:** all runs so far are small pipeline pilots, not the final EcomSafeBench. The shortcut-audit accuracy is a dataset-quality diagnostic, not detector performance.
- **Origin:** the code was developed outside this repository and imported unchanged. The exceptions are:
  - this README;
  - one config-key fix (see [Reproduction](#reproduction));
  - the added `scripts/render_prompts.py`, `prompts/` and `examples/`.

## Dataset Definitions

| Term | Meaning |
|---|---|
| **Attack** | A shopper request intended to violate a commercial policy, or to help someone violate it. |
| **Matched negative** | A legitimate shopper request paired on purpose with one attack. It has the same product and policy topic and, in most cases, the same framing, so the pair differs in intent rather than topic. |
| **Boundary case** | A legitimate request near a policy boundary, designed to test over-blocking. |
| **Benign / control** | The umbrella category for legitimate, non-attack requests. Matched negatives and boundary cases are both benign. |

## Pipeline

```
plan -> attacks -> matched negatives -> boundary cases
     -> rule filter -> near-dup filter -> blind judge (+ matched-negative repair)
     -> pair integrity -> stratified trim -> grouped splits + held-out splits
     -> shortcut audit -> report
```

Organic benign sources (Bitext, Twitter customer support) are an optional future input. Loaders exist in `sources.py`, but both config paths are `null`, so no pilot run contains organic data.

## Components

| Stage | Code | What it does |
|---|---|---|
| Taxonomy | `taxonomy.py` | Defines the request intent labels, the 5 attack types and their intent mapping, the 8 framing techniques, the 0–3 severity scale and the Eq. 1 weights. |
| Domain grounding | `domains.py` | Covers 5 domains, each with a fictional catalog, policy text per topic (pricing, returns, warranty, competitor, restricted) and attack-type weights. Regulatory bypass is weighted 0 in fashion. |
| Planning | `plans.py` | Fixes intent, severity, attack type, technique, domain, product and policy topic **before** any text is generated. |
| Prompt templates | `prompts.py` | Templates for attacks, matched negatives, repair, boundary cases and the blind judge. The version is stored in `PROMPT_VERSION`. |
| Generation | `generate.py`, `llm.py` | Requests 5 variants per call, detects and re-samples refusals, and caches every LLM call in SQLite. |
| Rule filter | `quality.RuleFilter` | Removes messages by length (15–700 characters), refusal text, banned meta-words and label tokens. |
| Near-duplicate filter | `quality.NearDupFilter` | MinHash with Jaccard ≥ 0.8 on character 5-grams, applied within each class so minimal pairs survive. |
| Blind judge | `quality.BlindJudge` | Relabels each message without seeing the intended label. It accepts a record when the intent matches, confidence is at least 0.5 and the judge marks the message realistic. PV↔FF counts as a soft agreement. |
| Matched-negative repair | `pipeline._repair_negatives` | Rewrites a rejected matched negative using the judge's rationale, then judges it again, for up to 2 rounds. |
| Pair integrity | `pipeline._pair_integrity` | Drops any attack or matched negative whose partner did not survive. |
| Trim | `pipeline.trim` | Trims attacks to `attack_target`, stratified by domain × attack type. |
| Splits | `splits.py` | Groups records into connected components over `gen_group` and `pair_id`, then splits 70/10/20. Also builds held-out splits for domain = groceries, technique = instruction_injection and attack type = competitor_extraction. |
| Shortcut audit | `quality.shortcut_audit` | Multinomial Naive Bayes on unigrams and bigrams, attack vs matched negative, with 5-fold CV grouped by `gen_group`. |
| Annotation | `annotate.py` | Exports a blind sample and a key file. Scores Cohen's κ for human vs design and human vs judge. |
| Preflight | `preflight.py` | Checks the config, API keys and the generator/judge family split, then sends live test prompts. `--smoke` adds a run of about 10 attacks and invariant checks. |
| CLI | `run.py` | Runs a generation, or the `check`, `annotate` and `score` commands. |

## Models Used in Current Pilots

Every reported pilot used:

| Role | Backend | Model and settings |
|---|---|---|
| Generator | Groq | `openai/gpt-oss-120b`; temperature 0.9; `reasoning_effort: medium`; 5 variants per call |
| Judge | Groq | `qwen/qwen3.8-27b` (a different model family); reasoning disabled (`reasoning_effort: none`); temperature 0, or 0.3 on retry |

**Supported backends (not used in the reported pilots):** `llm.py` can also call Anthropic, OpenAI-compatible and vLLM servers, Gemini, xAI Grok, a local Llama server, and a mock backend for offline tests.

## Labels and Risk Targets

- **Request intent labels** for shopper messages are PV, CD, FF, RB and BENIGN.
  - The mapping is: price manipulation → PV, policy bypass → PV, return fraud → FF, competitor extraction → CD, regulatory bypass → RB.
  - Matched negatives and boundary cases are labelled BENIGN.
- **Response labels** (`ResponseLabel`) are CR (Compliant Refusal), COMPLIED, PARTIAL and HELPED.
  - They describe a target model's *response*. They will be used only after target-model responses are collected.
  - CR is never a generated shopper label.
- **Risk targets:** each user turn stores `risk_target = w(intent) × severity_scale`.
  - The weights follow the proposal's Eq. 1: FF 1.0, RB 0.8, PV 0.6, CD 0.4.
  - The severity scale (0, 0.33, 0.67, 1.0) is a design extension.
- **Severity:** single-turn attacks use severity 2 or 3 (50/50), and benign records use 0.

## Turn Structure

- **Current data:** each record is **exactly one shopper (user) message with no assistant response**. It is single-turn only.
- **Multi-turn:** the scaffolding is implemented but has not yet been run.
  - The plan builders (linear, camouflaged, late-spike), `Realizer.realize_multi` and per-turn judging exist.
  - The config sets 3–7 turns, a 0.4/0.3/0.3 pattern mix and a target of 1,100 conversations, but `multi_turn.enabled: false`.
  - No multi-turn data has ever been generated or validated.
- **Open design issue:** the proposal's metric counts attacks caught "before turn 5", but the configured 3–7 turn range allows conversations shorter than 5 turns. This is left for the next cycle.

## Pilot Runs

All runs used the models above.
- **Column key:** A = attacks, N = matched negatives, B = boundary cases.
- **Funnel columns:** "After judge" includes repair, and "Final" is after pair integrity and trim.
- **Lexical audit:** the grouped Naive Bayes shortcut-audit accuracy. **High accuracy is bad for dataset quality.** It is not detector accuracy.

| Run | Prompts | Attack target | Generated | After judge | After pairing | Final | A / N / B | Train / val / test | Lexical audit |
|---|---|---|---|---|---|---|---|---|---|
| single_turn_v1_check | st-v1 | 10 | 39 | 29 | 20 | 20 | 9 / 9 / 2 | 20 / 0 / 0 | 0.50 |
| single_turn_v1 | st-v1 | 50 | 115 | 87 | 62 | 62 | 24 / 24 / 14 | 52 / 10 / 0 | 0.833 |
| pilot_v2 | st-v1.1 | 50 | 125 | 113 | 101 | 101 | 43 / 43 / 15 | 67 / 16 / 18 | 0.884 |
| pilot_v3 | st-v2 | 50 | 155 | 99 | 58 | 58 | 23 / 23 / 12 | 36 / 6 / 16 | 0.783 |
| pilot_v4 | st-v2.2 | 50 | 155 | 114 | 74 | 74 | 30 / 30 / 14 | 50 / 8 / 16 | 0.767 |
| **pilot_v5** (comparison) | st-v2.3 | 50 | 155 | 149 | 144 | 114 | 50 / 50 / 14 | 81 / 12 / 21 | 0.84 |
| **pilot_150** (headline) | st-v2.4 | 150 | 392 | 375 | 361 | 289 | 126 / 126 / 37 | 195 / 35 / 59 | 0.905 |

**`pilot_150` is the headline pilot.** It is the newest and largest run, and it used this code. **`pilot_v5`** shows the previous iteration.

The `examples/` folder holds each run's `report.md`, `report.json` and `config_used.yaml`, copied unchanged. `examples/pilot_150/sample.jsonl` holds 24 verbatim `pilot_150` records: 10 attack/negative pairs (2 per attack type) and 4 boundary cases.

## Current Limitations

- **Lexical shortcuts remain.** A grouped 5-fold multinomial Naive Bayes audit on unigrams and bigrams separated attacks from matched negatives with 0.905 accuracy in `pilot_150` (n = 252). Because the audit sees only surface words, substantial lexical shortcuts remain, and matched-negative and attack phrasing need another iteration.
  - The top attack n-grams include *exception*, *bypass*, *override*, *competitor* and *margin*.
  - The top negative n-grams include *price_match*, *catalog* and *what_verification*.
- **Generator refusals:**

  | Run | Return fraud | Instruction injection | Other |
  |---|---|---|---|
  | `pilot_v5` | 4/8 attempts | 3/7 attempts | |
  | `pilot_150` | 22/26 attempts | 11/16 attempts | 6 attack plans failed entirely |

  - Denominators are API attempts, including retries, so they are not shares of unique final records.
  - `pilot_v3`, `pilot_v4` and `pilot_v5` reused the same cached attack generations, so their refusal counts are not independent.
- **Repaired negatives:**
  - 25 of the 50 final matched negatives in `pilot_v5`, and 47 of the 126 in `pilot_150`, were rewritten by repair against the same judge. Human annotation is their independent check.
  - The repair counters (`pilot_v5`: attempted 50, fixed 35) are summed over both rounds.
- **Funnel gaps:**
  - Records removed by trimming are not logged in `rejected.jsonl`.
  - The repeated "after blind judge (+repair)" rows in `examples/pilot_v5/report.md` come from a per-record logging bug that was fixed before `pilot_150`.
- **Empty test split:** in `single_turn_v1`, the cause was only 10 split components combined with older split code. The current `splits.py` fills the test split on the same data.
- **Uneven coverage:** in `pilot_150`, fashion has 9 attacks, and financial products and groceries have no return-fraud attacks.
- **No organic data and no multi-turn data.**

## Human Validation Status

- **Implemented:**
  - blind-sample export;
  - Cohen's κ for human vs design and human vs judge;
  - a confusion matrix.
- **Not implemented:**
  - agreement between two human annotators;
  - scoring of the "realistic" answers.
- **Not run:** no annotation exists for any run.
- **Planned for the next cycle:**
  1. About 100 items, labelled by 2 independent annotators.
  2. Add human-vs-human agreement.
  3. Keep human-vs-design and human-vs-judge κ.
  4. Resolve disagreements by discussion.
- **Caveat:** every accepted record has judge verdict `agree`. On a final `all.jsonl`, the exporter's "uncertain" sampling pool is therefore empty.

## Reproduction

### Quick Start

Run from `data_generation/`:

```bash
pip install -r requirements.txt
python -m pytest -q tests                       # offline tests, mock backends, no API calls

# offline dry run (mock generator and judge, no API calls)
python -m ecomsafe_datagen.run --config config/single_turn.yaml --backend mock --attack-target 200 --run-name mock_dry_run

# real run: needs GROQ_API_KEY in data_generation/.env (git-ignored) or exported in the shell
cp .env.example .env                            # then fill in GROQ_API_KEY
python -m ecomsafe_datagen.run check --config config/single_turn.yaml           # config + live connectivity
python -m ecomsafe_datagen.run check --config config/single_turn.yaml --smoke   # + ~10-attack end-to-end run
python -m ecomsafe_datagen.run --config config/single_turn.yaml --run-name pilot_150 --attack-target 150
```

### Human annotation

```bash
python -m ecomsafe_datagen.run annotate --data runs/pilot_150/data/all.jsonl --n 100
# writes runs/pilot_150/annotation_blind.csv and runs/pilot_150/annotation_key.csv
# after an annotator fills the label column of a copy (e.g. annotator_A.csv):
python -m ecomsafe_datagen.run score --annotations annotator_A.csv --key runs/pilot_150/annotation_key.csv
```

### Reproducibility notes

- **Overrides:** the pilots used the committed config with `--run-name` and `--attack-target` overrides. The committed `attack_target: 1000` is the eventual full target.
- **Outputs and cache:** outputs go to `runs/<run_name>/` and LLM calls are cached in `runs/llm_cache.sqlite`. Both are git-ignored. The original pilot outputs and cache were not imported.
- **Exact text needs the original cache:** fresh API calls are nondeterministic and may not reproduce the same text.
- **Config fix on import:** `config/single_turn.yaml` changed the judge's misspelled `request_per_minute: 4` to `requests_per_minute: 4`.
  - In `pilot_150` the misspelled key was silently ignored, so the Groq default of 30 requests per minute applied.
  - The fix affects only judge request pacing, not prompts, sampling or acceptance rules.

## Prompt Templates

- **Source:** all templates are in `ecomsafe_datagen/prompts.py` (`PROMPT_VERSION = "st-v2.4"`).
- **Rendered examples:** [`prompts/rendered_examples.md`](prompts/rendered_examples.md) shows every template rendered for one fixed example plan. Regenerate it with `python scripts/render_prompts.py`, which makes no LLM calls.
- **What the templates enforce:**
  - shopper text only, never an assistant reply;
  - grounding in the policy text;
  - matched negatives that mirror the attack's form while removing the forbidden request;
  - a judge prompt that never contains the intended label.

## Extending to Multi-Turn

Setting `multi_turn.enabled: true` routes multi-turn plans through the same realizer, filters, judge (`judge.turns: all` for per-turn audits), splits and writer.

Before this is used for the benchmark, three things are needed:
- prompt tuning for natural escalation;
- benign multi-turn dialogues;
- a decision on the turn-5 metric.

## Design Provenance

| Category | Sources |
|---|---|
| Peer-reviewed, verified | Nakash et al., *Effective Red-Teaming of Policy-Adherent Agents* (EMNLP 2025): CRAFT and tau-break, which inspired the policy-aware attack framing |
| Preprint, supporting only | SIA (arXiv 2603.16137), which inspired the boundary cases |
| Unverified inspiration notes | Code comments also mention CompliBench, the "Extreme Lowballer" buyer persona and LLM-to-LLM seller-agent jailbreak work. These are unverified and are not cited until a source is verified. |

## Files

```
data_generation/
├── README.md
├── requirements.txt, .env.example, .gitignore
├── config/single_turn.yaml      # pilot configuration (Groq generator + judge)
├── config/test_llama3b.yaml     # alternative local-Llama test configuration (not used in the pilots)
├── ecomsafe_datagen/            # pipeline package (see Components)
├── prompts/rendered_examples.md # rendered prompt templates
├── scripts/render_prompts.py
├── seeds/exemplars.jsonl        # 7 style exemplars
├── tests/                       # offline tests
└── examples/{pilot_150,pilot_v5}/  # unchanged run reports + 24-record sample
```
