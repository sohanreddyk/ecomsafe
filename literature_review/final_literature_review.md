# Multi-Turn Safety Detection for E-Commerce Conversational Agents: A Focused Literature Review

**Target proposal:** *Cart Before the Harm* (EcomSafe) [EcomSafe]
**Prior work:** Cognitive Firewall [CF], MultiTurnPSB [PSB], State-Dependent Safety Failures [SDSF]

## 0. Scope and conventions
This review draws only on the four provided PDFs. The CF copy covers only the abstract, the introduction, and part of Related Work (2 pp.).

| Tag | Meaning |
|---|---|
| `[X p.N]` | Source claim, page in the provided PDF; `(Table/Fig. N)` gives the origin of a value |
| **[VI]** | Verified visually from the page image |
| **[AMB]** | Ambiguous in source (the glyph is blank in both the OCR and original images) |
| **[NV]** | Not verifiable from provided copy |
| **[2nd]** | Secondhand description of a work that was not provided |
| *Interpretation:* | Reviewer analysis, not a source claim |

## 1. Prior work in brief
**CF** (Guida et al., arXiv:2607.01277v1) proposes an independent oversight model with four categorical gates. The intent, zero-trust context, and consistency gates act before generation; an output-risk gate inspects candidate responses. Verdicts are combined "through escalation rather than score averaging" [CF p.1–2]. Its datasets, models, method details, and results are **[NV]**. That includes the abstract's attack-success figures (≤2% on three sets, 14% on the human-crafted set) and its 8% over-refusal rate [CF p.1].

**PSB** (Sheoran & Hao, arXiv:2606.02630v1) turns 466 PatientSafetyBench prompts into 4-turn dialogues. It compares fixed-template, template-adaptive, and live adversarial attacks on GPT-4.1-mini and Claude Sonnet 4.5, scored by a GPT-4o-mini judge that sees only the current turn [PSB p.2–3]. It then evaluates an input-side six-way classifier that prepends a safety tag to the user message [PSB p.3].

**SDSF** (Li et al., ICML 2026, PMLR 306) introduces STAR (name **[VI]**), a diagnostic framework. It treats dialogue history as a state-transition operator over a latent state z_t (**[VI]**) [SDSF p.2–3]. STAR combines initialization (softening, persona, template) with evolution (role-conditioned turns, refusal-replacing history intervention, Δ-based retry) [SDSF p.4–5]. It evaluates five targets on HarmBench (50) and JailbreakBench (100) [SDSF p.5], with white-box analysis on Llama-3-8B-IT only [SDSF p.8]. Several subscript operators in Eqs. 1, 4, 5, 7, 8 are **[AMB]**.

Per-dimension details are in `comparison_table.md`.

## 2. Thematic synthesis

### 2.1 Why single-turn evaluation fails
All three papers reject message-level evaluation, on different evidence:
- **Behavioral divergence.** Defenders that are statistically indistinguishable at T1 (34.8% vs 31.8%, p = .43; test statistic **[AMB]**) end up 19× apart by T4 (78.8% vs 4.1%) (PSB Table 4 p.4; Fig. 3 p.5 **[VI]**).
- **Attack-success gaps.** Claude 3.5 Sonnet falls to 3.0% of attacks under GCG and PAIR but 74.0% under STAR (SDSF Table 1 p.6).
- **An architectural argument.** Deployed guard classifiers "all judge each message in isolation" [CF p.2, 2nd].

*Interpretation:* the causes differ: user pressure (PSB), self-conditioning on prior compliant outputs (SDSF), and missing intent, memory, and authority verification (CF). EcomSafe names only isolated input evaluation [EcomSafe p.1].

### 2.2 Escalation and risk accumulation
Damage concentrates early. PSB's live attack rises from 34.8% to 77.7% at T2 and then plateaus (Table 2 p.3), making T2 a "critical vulnerability window" [PSB p.4]. SDSF describes a first-turn "large displacement" into the compliance region and concludes that failure "does not require gradual erosion" (Fig. 5 p.8 **[VI]**).

Adaptive tactic *selection* outweighs rewording (a 19.1 pp gap) [PSB p.3], and emergency framing plus an authority claim underlies many catastrophic failures [PSB p.3–4]. History accumulation is the largest ablation factor (−25.5, Fig. 2 p.7 **[VI]**), and order matters: shuffling lowers the mean score from 5.00 to 4.11 (Fig. 3 p.7 **[VI]**). The same attacker yields rising or falling trajectories depending on the defender [PSB p.4–5].

*Interpretation:* EcomSafe's taxonomy (linear, camouflaged, late spike) [EcomSafe p.2] does not capture the dominant early step change well. No source studies camouflaged escalation directly.

### 2.3 State-dependent and trajectory-based modeling
SDSF reports suppressed refusal-direction projections and latent crossings on Llama-3-8B-IT (Figs. 4–5 p.8). Two caveats apply:
- **Fig. 4 disagrees with the text.** The text calls 2.35 → 0.13 → 0.08 → −0.0081 "final-layer" values [SDSF p.8], but in Fig. 4 **[VI]** they match layer ~12. At the final layer the values are non-monotonic, and the baselines lie below STAR.
- **Figs. 6–7 conflate two measures.** They mix "Alignment Score" with "mutual information" (p.12–13 **[VI]**).

CF lists TurnGate, THRD, CivicShield, and TCA as trajectory-aware (Table I p.2 **[VI]**; blank = present, a strong inference). It describes THRD as a "time-decayed composite" of per-turn risk and history [CF p.2, 2nd], and it criticizes reducing a conversation "to a single score" [CF p.2].

*Interpretation:* SDSF supports EcomSafe's RQ1 premise only indirectly: one model, attack trajectories only, and a figure/text inconsistency. EcomSafe's features (Δ, μ, σ, τ) summarize a *scalar* per-turn risk, whereas SDSF argues for a multi-dimensional signature [SDSF p.9].

### 2.4 Classifier-based defenses
PSB is the only paper that measures a classifier defense. On single turns its classifiers reach 93.3% (Claude) and 82.3% (GPT) accuracy (Table 6 p.6). Under adversarial history, accuracy falls from 95.5% to 48.5%, mainly through lateral category confusion (3.7% → 50.0%), not missed detection (Table 8 p.7). Lateral errors converge on Unlicensed Practice (55% → 71%, Fig. 5 p.7 **[VI]**). Even so, tagging cut T4 unsafe outputs from 78.8% to 26.6% (−52.2 pp) [PSB p.6–7].

*Interpretation:* lateral drift bears directly on EcomSafe Eq. 1, which gives the intents fixed, unequal weights [EcomSafe p.2]. Drift from FF to CD would lower r_t by 60% even if harmfulness is unchanged. No source tests whether hidden-state probes resist this drift better than text classifiers. The zero weight on CR also ignores SDSF's evidence that refusals in history are protective (3.60–3.98, Fig. 3 p.7).

### 2.5 Proactive and session-level guardrails
CF alone proposes pre-generation, session-level blocking, but its efficacy is **[NV]** [CF p.1]. PSB recommends combining input classification with output review and conversation-level detection [PSB p.6]. SDSF proposes, but does not build, early interception plus joint-signal monitoring [SDSF p.9].

*Interpretation:* EcomSafe's OR rule (TR > θ_traj or r_t > θ_local) [EcomSafe p.3] is consistent with CF's escalation argument, but its weighted sum within a turn is the averaging CF criticizes. The proposal does not say whether the probe reads states before or after generation. No source addresses cross-user attacks (EcomSafe TC3) [EcomSafe p.2].

### 2.6 Early detection
The sources place the decisive window at T2 [PSB p.4, p.6], in turns 1–2 through an "initialization signature" [SDSF p.9], or at "the earliest harm-enabling turn" (TurnGate) [CF p.2, 2nd].

*Interpretation:* EcomSafe's "before turn 5" metric [EcomSafe p.3] would credit detections that arrive after the harmful response in both regimes. Lead time relative to the first harmful turn is more informative. Trend features such as τ_t and μ_t need several turns before they carry signal.

### 2.7 False positives and deployment
PSB reports 45% (GPT) and 16% (Claude) false alarms on XSTest benign prompts, which it calls the "primary deployment constraint" (Table 6 p.6; p.1). CF's 8% over-refusal is **[NV]**. SDSF warns that benign dialogues also occupy low refusal-activation regions [SDSF p.9].

The sources also flag pipeline pitfalls:
- A current-turn-only judge cannot score escalation [PSB p.7].
- Safety-trained attackers self-refuse (53.9% at T4, Table 5 p.5); SDSF uses a helpful-only generator [SDSF p.5].

No source reports defender latency.

*Interpretation:* EcomSafe's generic benign set [EcomSafe p.3] may understate FPR without borderline-benign cases. ROC AUC on a 2,400:1,500 attack-to-benign split does not reflect deployment operating points.

### 2.8 Research gaps
Across the provided sources, the following are missing:
1. A commercial/business-rule taxonomy. Fraud-adjacent harms nonetheless appear in general benchmarks (SDSF Fig. 6 p.12; p.15).
2. A measured hidden-state detector over trajectories.
3. Benign controls for representational signals.
4. Latency evaluation.
5. Cross-session analysis.
6. Conversation-level judging.
7. Explicit authority-claim handling in EcomSafe, despite its "I'm a nurse" example [EcomSafe p.2; CF p.1; PSB p.3–4].

## 3. Positioning EcomSafe

**Direct overlap:** the escalation motivation (all three); a per-turn category classifier across turns (PSB); hidden-state change across turns (SDSF); escalation-style session blocking (CF); trajectory-aware per-turn-risk aggregation (THRD/TurnGate [2nd]).

**Plausibly distinctive** (*interpretation*): the commercial taxonomy and EcomSafeBench; a white-box probe feeding an *incremental* trajectory model; explicit Δ/μ/σ/τ features; latency (RQ5); cross-domain analysis (RQ4).

**Well supported:**
- **Strong:** multi-turn escalation defeats single-turn filters (PSB Tables 2 and 4; SDSF Table 1).
- **Strong as motivation:** false positives matter (PSB Table 6).
- **Moderate:** hidden states shift (SDSF Figs. 4–5); imperfect per-turn signals still reduce harm (PSB Table 8).

**Risky claims:**
1. That existing guardrails lack risk-accumulation tracking [EcomSafe p.1]. This is contradicted by CF Table I [VI] and THRD [2nd]. It should be restricted to message-level guard classifiers.
2. That trajectory-awareness itself is the novelty. The contribution must rest on the combination listed above.
3. That detectors "fail in these environments" [EcomSafe p.1]. This is untested.
4. That τ_t detects monotonic trends and σ_t detects camouflage [EcomSafe p.3]. These are design intentions.
5. Any implication that probes are more robust than text classifiers. There is no evidence either way.
6. "Commercial jailbreaks" should be framed as a systematic taxonomy and benchmark, not as the first appearance of these harms.

**Necessary experiments** (P1; details in `gap_analysis.md`):
- single-turn vs trajectory detection on the same conversations;
- THRD-style and TurnGate-style baselines;
- detection lead time relative to the first harmful turn, with turn-level annotation;
- FPR at fixed recall on generic and borderline-benign sets;
- p50/p95 per-turn latency.

**Recommended** (P2): Eq. 1/Eq. 2 ablations by turn index; probe-drift analysis; abrupt-escalation stress tests; history-perturbation tests; benign representational analysis; an attack-generation audit.

**Unresolved from the provided material:** CF §III–VI **[NV]**; the internals of THRD, TurnGate, CivicShield, TCA, and LlamaFirewall **[2nd]**; the PSB test statistic and threshold comparator, and the SDSF subscript operators, auxiliary-model subscript, and threshold symbol **[AMB]**.

## References
- **[EcomSafe]** J. Koshal, S. Sushmita. "Cart Before the Harm: Multi-Turn Safety Detection in E-Commerce Conversational Agents." Proposal, Northeastern University, May 29, 2026.
- **[CF]** M. Guida et al. "Cognitive Firewall: A Proactive, Zero-Trust, Multi-Gate Framework for LLM Safety." arXiv:2607.01277v1, 2026 (incomplete 2-page copy).
- **[PSB]** [A]nushka Sheoran, Y. Hao. "MultiTurnPSB: Evaluating Multi-Turn Jailbreak Attacks and Classifier-Based Defenses for Medical AI Safety." arXiv:2606.02630v1, 2026.
- **[SDSF]** P. Li et al. "State-Dependent Safety Failures in Multi-Turn Language Model Interaction." ICML 2026, PMLR 306; arXiv:2603.15684v2.
