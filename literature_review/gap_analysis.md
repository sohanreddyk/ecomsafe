# Gap Analysis: Positioning EcomSafe Against Prior Work

Tags: `[p.N]` = page in the provided PDF · **[VI]** = verified visually from a page image · **[AMB]** = ambiguous in source · **[NV]** = Not verifiable from provided copy · **[2nd]** = secondhand. Unless a sentence carries a source tag, it is reviewer interpretation.

---

## 1. Direct overlap
Places where a prior paper already does substantially what EcomSafe proposes.

| EcomSafe element | Overlapping prior work | Evidence |
|---|---|---|
| Core motivation: per-turn guardrails miss multi-turn escalation [EcomSafe p.1] | All three papers | CF p.1–2; PSB p.1, p.6; SDSF p.1, p.6 |
| A per-turn *category* classifier as the safety signal, evaluated across turns [EcomSafe p.2] | PSB's six-way category classifier with a Phase-2 drift analysis | PSB p.3, p.6–7 (Tables 6–8) |
| Hidden-state change across conversation turns (RQ1) [EcomSafe p.1] | SDSF refusal-direction and latent-trajectory analysis on Llama-3-8B-IT | SDSF p.8 (Figs. 4–5) |
| Session-level blocking with an escalation-style OR rule [EcomSafe p.3] | CF escalation-based gate combination; pre-generation blocking | CF p.1–2 |
| Trajectory-aware aggregation of per-turn risk [EcomSafe p.3] | THRD ("per-turn risk, historical context… one time-decayed composite"); TurnGate ("blocks at the earliest harm-enabling turn") | CF p.2 [2nd]; Table I [VI] |
| Regulatory Bypass / pharmaceutical domain [EcomSafe p.2–3] | PSB unlicensed-practice and harmful-advice categories | PSB Table 1 p.2 |

## 2. Partial overlap

| EcomSafe element | Partial counterpart | How it differs |
|---|---|---|
| Hidden-state *probe* producing intent probabilities [p.2] | SDSF projects onto one refusal direction [p.8] | SDSF analyzes but does not detect; one direction, not a multi-intent probe; no benign controls |
| Trajectory features Δ, μ, σ, τ [p.3] | SDSF uses Δ_t on the attack side [p.4–5]; PSB describes trajectory *shapes* [p.4–5] | Neither uses these statistics as detector inputs |
| Early-detection metric [p.3] | PSB's Turn-2 window [p.4, p.6]; SDSF's initialization signature in turns 1–2 [p.9]; TurnGate earliest-turn blocking [CF p.2, 2nd] | EcomSafe's cutoff ("before turn 5") is looser than the windows these works identify |
| FPR on benign dialogues [p.3] | PSB XSTest false alarms [p.6] | PSB's benign set is single-turn and borderline; EcomSafe's is multi-turn and generic |
| Commercial fraud harms [p.2] | SDSF's fake-Amazon-reviews example (Fig. 6, p.12); its judge policy lists "Fraudulent or deceptive activity" (p.15) | Present inside general benchmarks, but with no commercial taxonomy |
| Authority claims inside attacks (the "I'm a nurse" example) [p.2] | CF zero-trust context gate [p.1]; PSB authority tactic [p.2–4]; SDSF personas [p.4] | EcomSafe has no authority-specific feature or gate |

## 3. Major differences (what EcomSafe does that the provided priors do not)
1. **A commercial / business-rule threat taxonomy.** Price manipulation, policy bypass, return fraud, competitor extraction, and regulatory bypass (Table 1, p.2). No provided prior work targets business-logic violations as distinct from harmful content.
2. **A multi-domain commerce benchmark.** EcomSafeBench, 3,900 conversations across 5 product domains [p.3].
3. **A white-box probe feeding an *incremental* trajectory model** (Eq. 2, p.3). PSB's detector is a black-box LLM prompt [PSB p.3]. SDSF builds no detector [SDSF p.9]. CF's mechanism is [NV].
4. **Explicit latency evaluation** (RQ5) [p.1, p.3]. None of the priors reports it.
5. **Per-domain and per-threat-class analysis** (RQ4) [p.1]. PSB does per-category analysis within medicine (Table 3, p.3), but not across domains.

## 4. Unresolved gaps
These are gaps that neither the prior work nor the current EcomSafe proposal resolves.

| # | Gap | Evidence it is open | Status in EcomSafe |
|---|---|---|---|
| G1 | **Cross-user / coordinated attacks** | Absent from all three priors | Named as TC3 [p.2], but the architecture is per-session (Eq. 2) [p.3]. *No mechanism.* |
| G2 | **Benign separability of hidden-state signals** | SDSF asserts benign interactions lack the joint signature but shows no benign experiment [SDSF p.9] | 1,500 benign dialogues [p.3] could close this, if representational analysis covers benign sessions too |
| G3 | **Abrupt vs gradual escalation** | Abrupt T2 jump (PSB Table 2 p.3); single-step crossing (SDSF Fig. 5 p.8) | Taxonomy emphasizes linear/camouflaged/late spike [p.2]; τ_t and μ_t favor gradual trends |
| G4 | **Probe drift under adversarial history** | PSB accuracy 95.5 → 48.5%, mostly lateral (Table 8 p.7) | Not evaluated; Eq. 1's unequal weights make lateral drift change r_t |
| G5 | **Authority / persona manipulation** | CF p.1; PSB p.3–4; SDSF p.4, p.9 | No explicit feature |
| G6 | **Pre- vs post-generation detection point** | CF distinguishes pre-generation from output gates [p.1] | Unspecified whose hidden states the probe reads, and when [p.2] |
| G7 | **Attack-data generation validity** | Safety-trained attackers self-refuse, reaching 53.9% at T4 (PSB Table 5 p.5); SDSF uses a helpful-only generator [p.5] | EcomSafeBench generation and annotation are not described [p.3] |
| G8 | **Conversation-level labels** | The PSB judge sees only the current turn and "cannot score multi-turn escalation patterns" [PSB p.7] | "Annotated" is unspecified [p.3]; early detection needs turn-of-harm labels |
| G9 | **The agent's own responses as state** | SDSF: self-conditioning on prior compliant outputs drives failure; refusals in history protect (Fig. 3 p.7) | r_t is framed around user intent; the CR intent has weight 0 in Eq. 1 [p.2] |
| G10 | **History manipulation by the attacker** | SDSF's feedback-aware history intervention swaps refusals for surrogates (Eq. 7, p.4) | Not discussed. *Relevant only if clients can supply history, as with API access.* |

## 5. Which EcomSafe claims are well supported
| EcomSafe claim | Support | Strength |
|---|---|---|
| Adversaries escalate across turns in which each turn looks benign [p.1] | PSB Table 2 p.3; SDSF Table 1 p.6; CF p.1 | **Strong** (three independent sources, two with data) |
| Single-turn filters are insufficient [p.1] | PSB Table 4 p.4 (19× divergence from equivalent baselines); SDSF Table 1 p.6 | **Strong** |
| Hidden states change across multi-turn attacks (RQ1 premise) [p.1] | SDSF Figs. 4–5 p.8 | **Moderate**: one model, and Fig. 4's text/figure inconsistency |
| Per-turn risk signals are useful even when imperfect [p.2] | PSB: a 48.5%-accurate classifier still cut T4 unsafe outputs by 52.2 pp (Table 8 p.7) | **Moderate** (an input-tag intervention, not detection) |
| An OR-rule combining local and trajectory thresholds [p.3] | CF's escalation-over-averaging argument [p.1–2] | **Conceptual only** (CF results are [NV]) |
| False positives on benign shopping matter [p.3] | PSB false alarms of 16–45% (Table 6 p.6) | **Strong** as motivation |

## 6. Risky novelty claims
1. **"Existing guardrails operate on single turns without tracking risk accumulation"** [EcomSafe p.1]. The CF copy lists four trajectory-aware defenses (TurnGate, THRD, CivicShield, TCA; Table I, p.2 [VI]). It describes THRD as fusing per-turn risk with history into a time-decayed composite [CF p.2, 2nd], which is conceptually close to EcomSafe's trajectory layer. *Recommendation:* restrict the claim to "deployed message-level guard classifiers" (as CF does, p.2). Position EcomSafe against trajectory-aware defenses rather than claiming to be the first.
2. **"Trajectory-aware sequence model" as the core novelty** (RQ2) [p.1]. Given (1), the novelty has to rest on the *combination*: hidden-state probe, incremental update, commercial domain, and latency. It should not rest on trajectory-awareness itself.
3. **"Current jailbreak detection methods fail in these environments"** [p.1]. No provided source evaluates any detector in an e-commerce environment. This is a hypothesis for EcomSafe to test, not an established fact.
4. **Kendall's τ "detects monotonic trends"** and σ_t "detects camouflaged escalation" [p.3]. These are design intentions. The priors suggest the dominant empirical pattern is an early step change (PSB p.3; SDSF p.8), not a monotonic trend. Neither claim has support yet.
5. **Hidden-state probing is more robust than text classifiers.** This is implicit, not stated. No provided source compares them, so avoid implying it.
6. **Commercial jailbreaks as a new threat class.** Largely defensible, since no provided prior work treats business-rule violations. However, fraud-adjacent harms (fake reviews: SDSF Fig. 6 p.12; the "fraudulent or deceptive activity" policy: SDSF p.15) and regulatory and medical bypass (PSB) already appear in general benchmarks. Frame the novelty as *systematic taxonomy plus benchmark*, not as the first appearance of these harms.

## 7. Experiments necessary to justify EcomSafe's contribution
Priority: **P1** = needed for the core claim; **P2** = strongly recommended; **P3** = strengthens the paper.

| # | Experiment | Addresses | Priority |
|---|---|---|---|
| E1 | **Single-turn vs trajectory detection on identical conversations**: isolated per-turn probe vs the full EcomSafe model, with ROC AUC per threat class | RQ2; claim §5 | P1 |
| E2 | **Strong trajectory-aware baselines**: full-context classifier, sliding-window max (already planned, p.3), plus a time-decayed per-turn-risk composite (a THRD-style reimplementation, described only secondhand in CF p.2) and an earliest-turn monitor (TurnGate-style) | Novelty risk §6.1–2 | P1 |
| E3 | **Detection lead time relative to the first harmful-response turn**, not only "before turn 5" | G3, G8; §2.6 of the review | P1 |
| E4 | **Turn-level harm annotation** of EcomSafeBench, with annotation protocol and agreement reported | G8 | P1 |
| E5 | **FPR at fixed recall** on (a) generic benign dialogues and (b) a *borderline-benign* set, such as legitimate returns of defective items, honest price-match requests, and pharmacist-style dosage questions (in the spirit of PSB's XSTest usage, p.2) | Deployment claim; PSB Table 6 | P1 |
| E6 | **Per-turn latency** of probe plus trajectory update on the target models, reported as p50/p95 | RQ5 | P1 |
| E7 | **Ablations of Eq. 1 and Eq. 2**: fixed weights vs learned vs max over harmful intents; with vs without CR; each of Δ, μ, σ, τ removed; results broken down by turn index | Claim §6.4; G4, G9 | P2 |
| E8 | **Probe-drift analysis**: per-intent accuracy and lateral confusion by turn (a PSB Phase-2 analogue, Table 8 p.7) | G4 | P2 |
| E9 | **Abrupt-escalation stress test**: attacks built with SDSF-style persona plus softening initialization (SDSF p.4), and PSB-style emergency-plus-authority framing (PSB p.3–4), adapted to commerce | G3, G5 | P2 |
| E10 | **History-perturbation tests on the detector**: shuffle, truncation, keep-last-k, inserted refusals (mirroring SDSF Fig. 3 p.7), to check that the detector uses order and trajectory rather than surface content | RQ3 | P2 |
| E11 | **Benign representational analysis**: hidden-state and refusal-direction trajectories for benign sessions vs attack sessions | G2; tests SDSF's unverified p.9 claim | P2 |
| E12 | **Attack-generation audit**: report the generator model and its refusal rate, and apply refusal detection or filtering (PSB p.5, p.7) | G7 | P2 |
| E13 | **Cross-model and domain transfer**: train on one Llama model or domain, test on another (RQ4) | RQ4 | P3 |
| E14 | **Cross-session aggregation prototype**, or explicitly drop TC3 from the scope | G1 | P3 (or remove the claim) |
| E15 | **Pre- vs post-generation placement**: detect on the user turn before generation vs on the agent response | G6 | P3 |

## 8. Items that cannot be resolved from the provided material
- The Cognitive Firewall's method, benchmarks, models, results, ablations, and limitations (§III–VI): **Not verifiable from provided copy**.
- The internals of THRD, TurnGate, CivicShield, TCA, and LlamaFirewall. They are known here only through CF's one-line descriptions and Table I [2nd].
- The symbols blank in both the OCR and original PDFs:
  - the PSB test statistic in "( = .63, p = .43)", and the unsafe-threshold comparator in the Table 2 caption;
  - the SDSF subscript operators in Eqs. 1, 4, 5, 7, 8, the auxiliary-model subscript, and the violation-threshold symbol.

  All are **Ambiguous in source**.
