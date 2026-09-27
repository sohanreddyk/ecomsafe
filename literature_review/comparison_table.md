# Comparison Table: EcomSafe vs Prior Work

Tags: `[p.N]` = page in the provided PDF · **[VI]** = verified visually from a page image · **[AMB]** = ambiguous in source · **[NV]** = Not verifiable from provided copy · **[2nd]** = secondhand (one paper's description of another work) · *italics* = reviewer interpretation.

## A. Core dimensions

| Dimension | EcomSafe (target) | Cognitive Firewall [CF] | MultiTurnPSB [PSB] | State-Dependent [SDSF] |
|---|---|---|---|---|
| **Paper type** | Proposal; no results yet [p.1–3] | Defense framework [p.1] | Benchmark plus defense evaluation [p.1] | Diagnostic attack framework plus interpretability [p.1–2] |
| **Domain** | E-commerce: electronics, pharma, fashion, financial, groceries [p.3] | General LLM safety [p.1] | Patient-facing medical [p.1] | General harmful content (HarmBench, JailbreakBench) [p.5] |
| **Threat focus** | Commercial jailbreaks; multi-turn escalation (linear, camouflaged, late spike); cross-user coordination [p.2] | Single-turn, multi-turn, authority-based, human-crafted [p.1] | Urgency, false authority, emotional pressure; live adaptive attacker [p.2–3] | Softening plus persona initialization, then role-conditioned evolution [p.4] |
| **Multi-turn horizon** | Unspecified; the early-detection metric uses "before turn 5" [p.3] | [NV] | 4 turns [p.2] | T_max = 7 [p.6] |
| **Access to model internals** | White-box hidden-state probe [p.2] | [NV] (oversight model reads the interaction) [p.1] | Black-box (LLM-prompted classifier) [p.3] | Black-box attack; white-box analysis on Llama-3-8B-IT only [p.8] |
| **Per-turn signal** | Intent probabilities PV/CD/FF/RB/CR → weighted scalar r_t (Eq. 1) [p.2] | Categorical gate verdicts (intent, context, consistency, output) [p.1] | 6-way category prediction [p.3]; judge score 1–5 [p.2] | Judge score J_t; Δ_t (Δ [VI]) [p.4]; refusal-direction projection [p.8] |
| **Trajectory signal** | f_θ over r_1…r_t with Δ_t, μ_t, σ_t, τ_t (Eq. 2) [p.3] | Consistency gate "audits the conversation so far" [p.1]; mechanism [NV] | None in the defense; trajectory *signatures* are descriptive only [p.4–5] | Latent z_t trajectory (z [VI]) [p.3, p.8]; history as a state operator [p.7–8] |
| **Aggregation logic** | Weighted sum within a turn; OR of TR > θ_traj and r_t > θ_local [p.2–3] | Escalation, "rather than score averaging" [p.1–2] | Tag whenever any harmful category is predicted [p.3] | N/A (no defense) |
| **Intervention** | Block, flag the session, or send to human review [p.3] | Pre-generation block plus output gate [p.1] | Input-side safety tag; no output filter [p.3] | Proposed only: early interception plus joint-signal monitoring [p.9] |
| **Authority / role handling** | Not modelled explicitly (the example "I'm a nurse…" is in Table 1) [p.2] | Zero-trust context gate [p.1] | Authority is a turn-3 tactic; part of the two-element formula [p.2–4] | Query-aware persona generation [p.4]; named-entity "anchors" [p.9, p.12] |
| **Output-side check** | Output safety filter used only as a *baseline* [p.3] | Output-risk gate [p.1] | Not included; recommended as future work [p.3, p.6] | N/A |
| **Cross-session analysis** | Threat Class 3 named [p.2]; no mechanism in the architecture | [NV] | No | No |
| **Latency measured** | Planned (RQ5) [p.1, p.3] | [NV] | No | No (attacker token cost only, Table 3) [p.6] |

## B. Data, models, metrics

| Dimension | EcomSafe | CF | PSB | SDSF |
|---|---|---|---|---|
| **Dataset** | EcomSafeBench, 3,900 conversations: 1,300 commercial, 1,100 escalation, 1,500 benign [p.3] | "four jailbreak benchmarks and a benign safety test set" [p.1]; names [NV] | PSB 466 prompts (464 used for the classifier) plus 100 XSTest benign [p.2–3] | HarmBench subset of 50; JailbreakBench 100 [p.5] |
| **Benign / over-refusal set** | 1,500 benign shopping and customer-service dialogues [p.3] | Benign safety test set [p.1]; [NV] | 100 XSTest safe prompts [p.2] | None |
| **How attacks are generated** | Not specified [p.3] | [NV] | GPT-4o-mini (templates and live), Claude Sonnet 4.5 (live) [p.2–3] | Qwen2.5-32B-Instruct, helpful-only [p.5] |
| **Labeling / judging** | Not specified ("annotated") [p.3] | [NV] | GPT-4o-mini judge, current turn only [p.2–3] | GPT-4o judge, 1–5 [p.5, p.15] |
| **Target models** | Llama-3.2-3B-Instruct, Llama-3.1-8B [p.3] | [NV] | GPT-4.1-mini, Claude Sonnet 4.5 [p.2, p.4] | GPT-4o, Claude 3.5 Sonnet, Gemini 2.0-Flash, Llama-3-8B-IT, Llama-3-70B-IT [p.5] |
| **Metrics** | ROC AUC per class; early-detection rate (before T5); FPR on benign; per-turn latency [p.3] | Attack success, over-refusal [p.1]; definitions [NV] | Unsafe rate per turn; mean score; accuracy, miss, false alarm, lateral error [p.3, p.6–7] | SFR; token cost [p.5] |
| **Baselines** | Per-turn classifiers, output filters, keyword filters, sliding-window max, full-context [p.3] | Guard models and trajectory-aware firewalls [p.2]; details [NV] | Two LLM classifiers compared (Claude vs GPT) [p.6] | GCG, PAIR, CodeAttack, RACE, CoA, Crescendo, X-Teaming, ActorAttack (Table 1) [p.6] |

## C. Headline quantitative evidence usable in the review

| Claim relevant to EcomSafe | Evidence | Source | Safe to cite? |
|---|---|---|---|
| Single-turn robustness does not predict multi-turn robustness | 34.8 vs 31.8% at T1 (p = .43) → 78.8 vs 4.1% at T4 (19×) | PSB Table 4 p.4; Fig. 3 p.5 [VI] | Yes (don't name the test statistic, which is [AMB]) |
| Multi-turn attacks far exceed single-turn ones | Claude 3.5: 3.0% (GCG/PAIR) vs 74.0% (STAR) | SDSF Table 1 p.6 | Yes |
| Most escalation damage happens early | Live attack 34.8 → 77.7% at T2 | PSB Table 2 p.3 | Yes |
| Boundary crossing can be abrupt | Two-phase trajectory; "single-step crossing" | SDSF Fig. 5 p.8 [VI] | Yes, qualitatively (t-SNE) |
| History order matters | Shuffle 5.00 → 4.11 | SDSF Fig. 3 p.7 [VI] | Yes |
| Classifiers drift under adversarial history | Accuracy 95.5 → 48.5%; lateral error 3.7 → 50.0% | PSB Table 8 p.7 | Yes |
| Even imperfect per-turn signals reduce harm | T4 unsafe 78.8 → 26.6% (−52.2 pp) | PSB Table 8 p.7; p.6 | Yes |
| False alarms constrain deployment | FA 45% (GPT), 16% (Claude) on XSTest | PSB Table 6 p.6 | Yes |
| Refusal-direction suppression across turns | Text: 2.35 → 0.13 → 0.08 → −0.0081 ("final layer") | SDSF p.8 vs Fig. 4 | **Caution:** these values match layer ~12 in Fig. 4 [VI], not the final layer |
| Role anchors produce abrupt coupling | Mean AS 0.147 → 0.208 → 0.282 | SDSF Fig. 6 p.12 [VI] | **Caution:** the paper mixes up the Alignment Score and MI labels |
| A pre-generation, escalation-based guard works | ≤2% ASR on 3 sets; 14% human-crafted; 8% over-refusal | CF abstract p.1 | **No: [NV]** (supporting results are not in the copy) |
| Trajectory-aware defenses already exist | THRD (time-decayed per-turn-risk composite), TurnGate (earliest-turn blocking) | CF p.2 [2nd]; Table I [VI] | Yes, as "described by CF"; the details are [NV] |

## D. Feature-level mapping (EcomSafe components → closest prior evidence)

| EcomSafe component [page] | Closest prior evidence | Support level (*interpretation*) |
|---|---|---|
| Hidden-state per-turn probe [p.2] | SDSF refusal-direction projection on Llama-3-8B-IT [p.8] | *Indirect; one model, attack trajectories only, figure/text inconsistency* |
| Intent taxonomy PV/CD/FF/RB/CR [p.2] | PSB 6-way category classifier [p.3] | *Analogous design; PSB shows lateral drift is the failure mode* |
| Fixed weights 1.0/0.8/0.6/0.4 (Eq. 1) [p.2] | None; CF argues against score averaging [p.1–2] | *Unsupported; needs ablation* |
| Δ_t (escalation delta) [p.3] | SDSF Δ_t = score differential used by the *attacker* for retry [p.4–5] | *Same quantity used on the defense side; plausible* |
| μ_t, τ_t (running mean, monotonic trend) [p.3] | PSB "compliance creep" is monotonic [p.4]; SDSF's crossing is abrupt [p.8] | *Mixed; trend features may lag abrupt crossings* |
| σ_t (volatility, for camouflaged escalation) [p.3] | SDSF baselines "oscillatory" near the boundary [p.8] | *No direct evidence for camouflage* |
| OR-threshold intervention [p.3] | CF escalation rule [p.1–2] | *Consistent with CF's argument* |
| Early-detection rate "< turn 5" [p.3] | PSB T2 window [p.4]; SDSF first-turn crossing [p.8] | *Threshold likely too lenient* |
| FPR on benign shopping dialogues [p.3] | PSB XSTest false alarms [p.6] | *Needs a borderline-benign set* |
| Latency (RQ5) [p.3] | None | *No prior baseline in the provided set* |
| Cross-user attacks (TC3) [p.2] | None | *No prior work and no architectural mechanism* |
