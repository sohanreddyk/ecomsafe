## Plan for Next Weeks

So far, the project consists of the proposal and report sections (related work, problem description, and threat taxonomy and dataset design). No code, data, or experiments exist yet. This cycle builds an end-to-end *pilot* of the EcomSafe pipeline on a small EcomSafeBench subset, using Llama-3.2-3B-Instruct, the smaller proposed target model. Pilot numbers are sanity checks, not reportable results.

| Days | Milestone | Deliverable | Success criterion |
|---|---|---|---|
| 1–2 | Repository and experiment setup | Repository layout (`data/`, `src/`, `configs/`, `results/`), pinned environment, and YAML config for model, seeds, and paths | A clean checkout installs and runs a smoke test that loads the model from config, with seeds fixed |
| 2–3 | Threat taxonomy implementation | Schema encoding the five attack types, three escalation patterns, five domains, five probe intents (PV/CD/FF/RB/CR), and annotation fields | Validator accepts valid examples and rejects malformed ones |
| 3–6 | EcomSafeBench pilot | About 150 conversations: 50 commercial jailbreaks (all five types), 40 escalations (all three patterns), and 60 benign, across all five domains, with turn- and conversation-level labels | Every conversation passes schema validation; the authors manually review all 150 and log and fix problems |
| 5–8 | Baselines | Isolated per-turn classifier, keyword and output safety filter, sliding-window max-risk, and full-context classifier behind one scoring interface | Each baseline scores every pilot turn without errors |
| 6–10 | Hidden-state probe prototype | Hidden-state extraction (one or more layers per turn), a linear intent probe, and per-turn risk *r*ₜ computed per Eq. 1 | Five intent probabilities and *r*ₜ are output per turn; probe accuracy on a conversation-grouped held-out split is reported with its sample size |
| 9–11 | Trajectory layer prototype | Trajectory features (Δₜ, μₜ, σₜ, τₜ) and a simple sequence model *f*θ with the OR-threshold rule | Unit tests on synthetic risk sequences give the expected values, e.g., τ = 1 on a strictly increasing sequence |
| 11–13 | Preliminary evaluation | Evaluation script and pilot report | All four metrics are computed for EcomSafe and the baselines on held-out pilot conversations: ROC AUC per threat class, early detection before turn 5, false-positive rate on benign dialogues, and p50/p95 per-turn latency |
| 14 | Review and buffer | Updated plan and a list of issues for the full benchmark | Open risks are documented, e.g., label ambiguity, class imbalance, and conversations too short for the turn-5 cutoff |

**Scope limits:**
- **Pilot size:** at roughly 10 conversations per attack type (about 2 per type–domain cell), pilot AUCs will have wide uncertainty and must not be presented as findings.
- **Second model:** Llama-3.1-8B, the second proposed target model, is deferred to the next cycle unless compute allows.
- **Extensions:** first-harmful-turn labels are prototyped in the schema but not required for the pilot metrics.
