# src/

**Scaffold for upcoming implementation. No implementation has been completed yet.**

This directory will hold the EcomSafe source code, planned for the next project cycle:

- **Hidden-state probe:** extracts per-turn hidden states from the target model (Llama-3.2-3B-Instruct for the pilot). A linear intent probe then predicts the five intents (PV, CD, FF, RB, CR), which are combined into a per-turn risk score.
- **Trajectory layer:** computes four features and feeds them to a simple sequence model with the OR-threshold intervention rule. The features are:
  - escalation-rate delta;
  - running mean risk;
  - risk volatility;
  - Kendall rank correlation with turn index.
- **Baselines:**
  - isolated per-turn classifier;
  - keyword and output safety filter;
  - sliding-window max-risk;
  - full-context classifier.
- **Evaluation utilities:** four metrics:
  - ROC AUC per threat class;
  - early-detection rate before turn 5;
  - false-positive rate on benign dialogues;
  - p50/p95 per-turn latency.

See the milestone plan in `paper/submission_update1/main.tex` (Plan for Next Weeks).
