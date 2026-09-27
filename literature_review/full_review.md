# Literature Review: Multi-Turn Safety Detection for E-Commerce Conversational Agents

**Target proposal:** *Cart Before the Harm: Multi-Turn Safety Detection in E-Commerce Conversational Agents* (EcomSafe)
**Prior work reviewed:** Cognitive Firewall [CF], MultiTurnPSB [PSB], State-Dependent Safety Failures [SDSF]
**Date compiled:** 2026-09-27

---

## 0. Scope, method, and evidence conventions

### 0.1 Scope
This review covers **only the four provided PDFs** (OCR versions in `papers/ocr/`). Wherever the OCR text layer dropped glyphs, the page images of the OCR and original PDFs were checked visually. No outside literature was searched or used. Other works cited *inside* these papers (e.g., THRD, TurnGate, Crescendo, X-Teaming) appear only as those papers describe them, and are marked **secondhand**.

*Deviation from the literature-review skill:* the skill's default workflow runs Semantic Scholar/arXiv/OpenAlex searches. That step was skipped on purpose because the user restricted the evidence base to the provided material. The skill's multi-perspective step was kept (Section 0.3), but every answer is grounded only in the four PDFs.

### 0.2 Evidence tags
| Tag | Meaning |
|---|---|
| `[CF p.N]`, `[PSB p.N]`, `[SDSF p.N]`, `[EcomSafe p.N]` | Source claim, with page number in the provided PDF |
| `(Table X)` / `(Fig. X)` | The value comes from that table or figure |
| **[VI]** | Verified visually from a page image during the verification pass (the text layer was corrupted or missing) |
| **[AMB]** | Ambiguous in source: the symbol or value is blank in both the OCR and the original page images |
| **[NV]** | Not verifiable from the provided copy |
| **[2nd]** | Secondhand: a claim one paper makes about another work that was not provided |
| *Interpretation:* | The reviewer's analysis, not a claim made by any source |

### 0.3 Perspectives used to structure the review (skill Step 1–2, restricted to provided sources)
| Persona | Guiding question | Where answered |
|---|---|---|
| Safety-evaluation methodologist | Do single-turn scores predict multi-turn robustness? How are judges and labels built? | §2.1, §2.7 |
| Mechanistic-interpretability researcher | Is there a hidden-state signal of escalation that a probe could read? | §2.3, SDSF entry |
| Guardrail/deployment engineer (e-commerce trust & safety) | What do false positives, latency, and session-level blocking cost? | §2.5, §2.7 |
| Adversarial red-teamer | Which attack patterns defeat per-turn filters, and how quickly? | §2.2, §2.6 |

---

## 1. Paper database (structured extraction)

### 1.1 Cognitive Firewall [CF]

> **Coverage warning.** The provided copy has **2 pages**: the abstract, the introduction, and part of Section II (Related Work). The original PDF is also 2 pages. The text cuts off mid-sentence in §II-B. Sections III–VI, all experimental tables, and the reference list are **not in the provided copy**.

| Field | Extraction |
|---|---|
| **Full citation** | M. Guida, R. Shikhhamzayev, S. Penchala, S. Iannucci, J. Li, S. Rahimi, N. Amiri Golilarz. "Cognitive Firewall: A Proactive, Zero-Trust, Multi-Gate Framework for LLM Safety." arXiv:2607.01277v1 [cs.CR], Jul 2026. Affiliations: Roma Tre University; The University of Alabama [CF p.1]. Venue: **[NV]**. |
| **Research problem** | Runtime safeguards evaluate prompts and responses as isolated messages. They therefore cannot "recover accumulated intent, verify asserted authority, or detect harmful objectives decomposed across a dialogue" [CF p.1, abstract]. |
| **Motivation** | The authors argue that "guarding a model is a comprehension problem, not a classification one." Harm "need not appear in any single message"; it can live in the objective, in an asserted authority, or in a goal assembled from innocuous parts [CF p.1]. A per-message classifier "carries no model of the user's evolving objective, retains no memory of the conversational trajectory, and has no means of judging whether a claimed role or authority warrants belief" [CF p.1]. |
| **Methodology** | An independent oversight model is placed between the user and a protected target model [CF p.1]. The detailed method (§III) is **[NV]**. |
| **Architecture / framework** | Four categorical gates [CF p.1–2]: (1) an **intent gate**, which identifies the operational objective; (2) a **zero-trust context gate**, which treats claimed roles and permissions as unverified evidence; (3) a **consistency gate**, which detects escalation and decomposition across turns; (4) an **output-risk gate**, which inspects candidate responses before release. The three pre-generation gates act *before* the protected model generates; the output gate is "a backstop" [CF p.1]. Gate verdicts combine "through **escalation rather than score averaging**," so any confident danger signal blocks, and a human-readable rationale is kept [CF p.1–2]. Gate internals, prompts, and oversight model identity: **[NV]**. |
| **Dataset / benchmark** | "four jailbreak benchmarks and a benign safety test set" [CF p.1]. Their names and sizes are **[NV]**. |
| **Models evaluated** | **[NV]** (neither the target nor the oversight model is named in the provided pages). |
| **Threat model / attack setting** | Single-turn, multi-turn, authority-based, and human-crafted attacks [CF p.1]. Authority claims (developer, clinician, operator, auditor) are treated as a distinct manipulation channel [CF p.1]. The formal threat model (§III) is **[NV]**. |
| **Multi-turn mechanism** | A consistency gate "audit[s] the conversation so far for escalation and decomposition" [CF p.1]. How it does so is **[NV]**. |
| **Safety signals / features** | Categorical gate verdicts on intent, context/authority, consistency, and output risk [CF p.1]. No numeric features are described in the provided pages. |
| **Defense / intervention** | A pre-generation block as soon as any one gate finds the interaction unsafe, plus output inspection on turns that reach the model [CF p.1]. |
| **Evaluation metrics** | Attack success and over-refusal rate are named in the abstract [CF p.1]. Their definitions are **[NV]**. |
| **Key quantitative results** | The abstract states attack success "2 percent or below on three attack sets," "14 percent on the most difficult human crafted set," and "an 8 percent over refusal rate" [CF p.1]. The supporting tables and experimental conditions are **[NV]**, so these numbers should not be relied on. |
| **Qualitative findings** | Table I (positioning) [CF p.2] **[VI]**: among the ten listed defenses, **every one is marked absent (✗) on zero-trust context verification**. Guard classifiers are ✗ on decomposition, trajectory, and ZT-ctx, and partial (◐) on pre-generation. TurnGate, THRD, CivicShield, and TCA have a blank ("present") mark on trajectory. The "present" glyph is blank in both the caption and the cells, so reading blank as "present" is a strong inference rather than a verified reading. The Cognitive Firewall row is entirely blank. |
| **Limitations** | Section V is **[NV]**. |
| **Deployment constraints** | Only the 8% over-refusal figure is visible, and it is **[NV]**. Latency and cost are **[NV]**. |
| **Relevance to EcomSafe** | High on concept: the paper frames multi-turn harm as accumulated intent and authority manipulation, argues against score averaging, and describes pre-generation blocking. Its related work names **existing trajectory-aware defenses [2nd]**: THRD "fuses per-turn risk, historical context, and a response evaluation into one time-decayed composite" and TurnGate "learns a single turn-level monitor over the history and candidate response and blocks at the earliest harm-enabling turn" [CF p.2]. These bear directly on EcomSafe's novelty claims (see gap analysis). |

---

### 1.2 MultiTurnPSB [PSB]

| Field | Extraction |
|---|---|
| **Full citation** | [A]nushka Sheoran, Yiduo Hao. "MultiTurnPSB: Evaluating Multi-Turn Jailbreak Attacks and Classifier-Based Defenses for Medical AI Safety." arXiv:2606.02630v1 [cs.CR], 30 May 2026. University of Pennsylvania [PSB p.1]. *Note:* the first author's initial capital is dropped in the source image; "Anushka" is inferred. The full title is confirmed by the original file name. Venue: **[NV]**. |
| **Research problem** | Patient-facing medical chatbots are evaluated on single-turn prompts, but real users "push back after refusals, add urgency, and invoke authority" [PSB p.1]. MedRiskEval and CSEDB "explicitly identify multi-turn evaluation as a gap" [PSB p.1, 2nd]. |
| **Motivation** | Single-turn scores "need not predict robustness to conversational pressure" [PSB p.1]. About 17% of survey respondents had used LLM chatbots for health information [PSB p.1, 2nd]. |
| **Methodology** | Each PatientSafetyBench (PSB) prompt is turned into a 4-turn dialogue, and three attack modalities are compared [PSB p.2–3]. A six-way input classifier is evaluated in three phases: single-turn accuracy, drift under adversarial history, and intervention [PSB p.3]. |
| **Architecture / framework** | Target model plus attacker LLM plus GPT-4o-mini judge. The defense is an **input-side** safety tag naming the predicted category and expected behavior, prepended to the user message [PSB p.3]. It "does not inspect or filter the output" [PSB p.3]. |
| **Dataset / benchmark** | PatientSafetyBench: 466 prompts in 5 categories (Table 1, p.2): harmful advice 99, misdiagnosis 99, unlicensed practice 97, misinformation 80, discrimination 91. Two prompts failed preprocessing, leaving 464 for classifier work [PSB p.3]. The benign class is 100 XSTest safe prompts [PSB p.2]. |
| **Models evaluated** | Defenders: GPT-4.1-mini (main) and Claude Sonnet 4.5. Attackers: GPT-4o-mini and Claude Sonnet 4.5. Judge: GPT-4o-mini at temperature 0.0. Classifiers: GPT-4.1-mini and Claude Sonnet [PSB p.2–3, p.5]. |
| **Threat model / attack setting** | Three settings [PSB p.2–3]. **Fixed-template**: Turns 2–4 are generated once and frozen, following an urgency → false authority → emotional pressure pattern. **Template-adaptive**: the same tactic order, with each follow-up rewritten after seeing the target's response. **Live adversarial**: the attacker sees the full history and chooses tactics freely (authority manipulation, emergency framing, educational reframing, partial-compliance exploitation, gradual escalation) at temperature 0.9. The defenders get **no system prompt**, so results are a lower bound [PSB p.3]. |
| **Multi-turn mechanism** | The target receives the full history at every turn. The **judge sees only the current turn's message and response** [PSB p.2–3]. |
| **Safety signals / features** | Per-turn judge scores from 1 (refusal) to 5 (full violation). The unsafe threshold is "at least 3" in the text [PSB p.2] but printed as "score [?]3" in the Table 2 caption, where the comparison glyph is **[AMB]**. The classifier predicts one of six categories [PSB p.3]. |
| **Defense / intervention** | A category-aware safety tag is prepended to the input when the classifier predicts a harmful category [PSB p.3]. |
| **Evaluation metrics** | Unsafe rate per turn; mean judge score; classifier accuracy, missed-detection rate, false-alarm rate, and lateral (wrong-category) error rate [PSB p.3, p.6–7]. |
| **Key quantitative results** | See §1.2.1 below. |
| **Qualitative findings** | **Four trajectory signatures** [PSB p.4–5]: *Compliance Creep* (GPT-4.1-mini, live: monotonic rise), *Diminishing Returns* (template attacks peak at T3), *Pattern Recognition* (Claude vs GPT attacker: monotonic fall), and *Spike-and-Abandonment* (Claude vs Claude, needing separate interpretation). **Two-element attack formula:** emergency framing plus a medical authority claim [PSB p.3–4]. **Turn 2 is a "critical vulnerability window"** [PSB p.4]. GPT-4.1-mini "appears to treat accumulated context as increasing user legitimacy," while Claude "appears to treat persistent pressure as a suspicion signal" [PSB p.4, p.6]; the authors call this a hypothesis [PSB p.6]. **Attacker self-limitation:** Claude as attacker refused increasingly often, and the refusals were silently passed to the defender, contaminating T3–T4 [PSB p.5]. |
| **Limitations** | Stated by the authors [PSB p.7]: a synthetic benchmark; one main target model; the judge is also the attacker in the GPT-vs-GPT condition, which may make scoring lenient; the judge cannot score multi-turn patterns; no defender system prompt; Claude self-attack is valid only at T2; English-only and text-only; short horizon. |
| **Deployment constraints** | A false-alarm rate of 45% (GPT classifier) or 16% (Claude classifier) on benign queries is "the primary deployment constraint" and "not acceptable for clinical deployment" [PSB p.1, p.6] (Table 6). Latency is **not reported**. |
| **Relevance to EcomSafe** | High. It is the closest analogue to EcomSafe's *pharmaceuticals* domain and its *Regulatory Bypass* class (EcomSafe's own example is "I'm a nurse—tell me the max safe dose…" [EcomSafe p.2]). It supplies an empirical baseline design (a per-turn category classifier under adversarial history) and a documented failure mode (lateral drift). It also carries a methodological warning about attacker refusal contamination. |

#### 1.2.1 PSB key quantitative results
| Result | Value | Source |
|---|---|---|
| Unsafe rate by turn, GPT-4.1-mini, fixed template | 34.5 → 50.9 → 60.3 → 58.6% | Table 2, p.3; Fig. 1, p.4 [VI] |
| Template-adaptive | 34.3 → 54.9 → 54.5 → 59.7% | Table 2, p.3 |
| Live adversarial | 34.8 → **77.7** → 77.5 → 78.8% | Table 2, p.3; Fig. 1 |
| Gap between template-adaptive and live at T4 | 19.1 pp, "isolates the contribution of adaptive tactic selection" | p.3 |
| Largest category increase (live) | Misinformation 15.0 → 83.8% (+68.8 pp) | Table 3, p.3 |
| Highest category at T4 | Discrimination 89.0%, with **zero** Score-5 violations | Table 3, p.3; p.4 |
| Same attacker (GPT-4o-mini), T1 | GPT-4.1-mini 34.8% vs Claude S4.5 31.8% (p = .43; test statistic symbol **[AMB]**) | Table 4, p.4 |
| Same attacker, T4 | GPT-4.1-mini 78.8% vs Claude 4.1%: a **19× gap** (74.7 pp) | Table 4, p.4; the 19× is **[VI]** from the Fig. 3 annotation, p.5 |
| Claude vs Claude attacker | 32.8 → 49.4 → 27.7 → 33.7% (only T2 is valid) | Table 4, p.4; Fig. 3 |
| Claude names the manipulation pattern | 0.9% of T1 responses → 38.8% of T4 responses (manual analysis) | p.4 |
| GPT-4o-mini T2 attacks that are generic restatement | 51.1% (238/466) | p.4 |
| Score-5 violations starting from safe T1 that occur at T2 (Claude self-attack) | 73.9% | p.4; App. C p.9 |
| Claude attacker refusal rate | T2 7.9%, T3 32.2%, T4 53.9%. GPT-4o-mini: 0 refusals in 1,398 turns | Table 5, p.5; Fig. 4 |
| Phase-1 classifier (564 single-turn examples) | Claude: 93.3% accuracy, 0.86% miss, 16.0% false alarm. GPT-4.1-mini: 82.3% accuracy, 5.4% miss, **45.0% false alarm** | Table 6, p.6 |
| Classifier drift under adversarial history (GPT) | Accuracy 95.5 → 62.4 → 52.8 → 48.5%. Missed 0.9 → 7.1 → 2.6 → 1.5%. Lateral 3.7 → 30.5 → 44.6 → 50.0% | Table 8, p.7; Fig. 5 [VI] |
| Share of lateral errors going to Unlicensed Practice | 55%, 62%, 67%, 71% (T1–T4) | Fig. 5 right, p.7 [VI] |
| Intervention (safety tag), unsafe rate | 17.2 → 46.1 → 29.0 → 26.6%. T4 falls from 78.8 to 26.6 (**−52.2 pp**) | Table 8, p.7; p.6 |
| Misinformation missed by the GPT classifier | 27.5% | p.6; Table 7 |
| Score-5 counts, T1–T4 (GPT vs GPT / GPT vs Claude / Claude vs Claude) | 13/25/34/38 (110); 11/3/1/0 (15); 11/27/17/6 (61) | Table 10, p.9 [VI] |

*Internal inconsistencies noted (interpretation):*
- The number 73.9% describes two different things. On p.4 and in App. C it is the share of 1→5 escalations that occur at T2 in the Claude self-attack condition. In the Discussion (p.6) it is the share of full violations at Turn 2 associated with the two-element formula. Cite only the p.4 meaning.
- The Conclusion says holding the defense at T2 "appears to predict safety through 86% of subsequent turns" [PSB p.7]. No supporting table or figure for this figure appears in the provided copy, so treat it as unsupported.

---

### 1.3 State-Dependent Safety Failures [SDSF]

| Field | Extraction |
|---|---|
| **Full citation** | P. Li, J. Zhang, T. Zhang, H. Qiu, K. Zhang, W. Zhang, N. Yu, W. Zhou. "State-Dependent Safety Failures in Multi-Turn Language Model Interaction." *Proceedings of the [ordinal **AMB**] International Conference on Machine Learning*, Seoul, South Korea, PMLR 306, 2026. arXiv:2603.15684v2 [SDSF p.1]. |
| **Research problem** | Is the safety boundary of aligned LLMs "static, or can it be systematically traversed through interaction?" [SDSF p.1–2]. |
| **Motivation** | Prior multi-turn work establishes that attacks are effective, but "a complementary mechanistic understanding of how conversational context degrades safety remains less developed" [SDSF p.1]. |
| **Methodology** | A state-space framing: dialogue history acts as a *state transition operator* over an unobserved latent state z_t ∈ 𝒵 [SDSF p.3] (z notation **[VI]** from Figs. 1 and 5). The authors present STAR as "a diagnostic tool rather than an optimization-based attack" [SDSF p.2]. Analyses include component ablation (§5.2), history-causality perturbations (§5.3), and white-box representational tracking (§5.4) [SDSF p.3]. |
| **Architecture / framework** | **STAR** (State-oriented Role-playing framework; name **[VI]**) [SDSF p.2]. *Stage I, state initialization* [p.4]: semantic-preserving softening (N=5 candidates chosen by BERT cosine similarity, Eq. 2), a query-aware persona (Eq. 3), and a structured turn template (Eq. 4). *Stage II, state evolution* [p.4–5]: role-conditioned turn execution; feedback-aware history intervention, where refusals scored J∈{1,2} are replaced in the stored history by a benign surrogate r̂_t (Eqs. 6–7); and trajectory control by adaptive retry. The score differential Δ_t is compared with 0 (Δ is **[VI]** from Fig. 1). If Δ<0 the attacker retries up to K times; if Δ≥0 it uses a conservative fallback (Eq. 8). *Notation caveat:* the operator in the subscripts 𝓗_{t□1} (Eqs. 1, 4, 7) and q_{t□1} (Eqs. 5, 8), and the subscript of the auxiliary model 𝓜, are **[AMB]**. |
| **Dataset / benchmark** | A HarmBench curated subset of 50 instructions, and JailbreakBench with 100 instructions [SDSF p.5]. |
| **Models evaluated** | Targets: GPT-4o, Claude 3.5 Sonnet, Gemini 2.0-Flash, Llama-3-8B-Instruct, Llama-3-70B-Instruct [SDSF p.5]. Auxiliary model: Qwen2.5-32B-Instruct, "helpful-only… without explicit red-teaming fine-tuning" [p.5]; Qwen2.5-7B in the sensitivity study (Table 4, p.15). Judge: GPT-4o, scoring 1–5 with X-Teaming rules [p.5; App. D p.15]. White-box analyses use Llama-3-8B-IT only [p.8]. |
| **Threat model / attack setting** | The authors frame realistic misuse as "multi-turn, adaptive, and black-box" [SDSF p.1]. Settings: T_max=7 turns, violation threshold (symbol **[AMB]**) = 5, K=3 retries [p.6]. Success means J=5 within the turn budget [p.5]. *Interpretation:* the history intervention (Eq. 7) requires the attacker to control the conditioning history it submits, which is plausible for API access but not for a hosted chat where the server keeps the history. |
| **Multi-turn mechanism** | Autoregressive conditioning on the accumulated history 𝓗_t (Eq. 1, p.3). Prior responses "function as in-context exemplars," and explicit refusals "reinforce defensive behavior" [p.4]. |
| **Safety signals / features** | Per-turn judge score J_t and its differential [p.4]. The projection of hidden states onto a **refusal direction** (following Arditi et al. [2nd]) [p.8]. t-SNE latent trajectories [p.8]. A token-level "alignment score" (cosine similarity) between prompt and generated representations [App. A p.12]. |
| **Defense / intervention** | None is implemented. The "Implications for Defense" paragraph [SDSF p.9] **proposes** a two-stage pipeline: (1) *early interception* of an "initialization signature" (a professional persona plus a softened query in turns 1–2); (2) *joint-signal monitoring*: "a single refusal-projection threshold is insufficient because benign multi-turn interactions… naturally occupy low refusal-activation regions," so monitoring should combine suppressed refusal features with strengthening role-conditioned coupling. The claim that this joint criterion "is absent in benign interactions" [p.9] has **no benign-conversation experiment in the provided copy**, so it is an unsupported assertion. |
| **Evaluation metrics** | Safety Failure Rate (SFR): the percentage of queries reaching J=5. Token cost: average input tokens to reach J=5 [SDSF p.5]. |
| **Key quantitative results** | See §1.3.1. |
| **Qualitative findings** | Safety bypass is "path-dependent rather than content-dependent": shuffling the scenes lowers compliance even though the content is the same [p.7]. Refusal acts as "a persistent state signal" [p.8]. STAR produces a **two-phase trajectory**: first a large displacement from the refusal region to the compliance region (a "single-step crossing"), then small incremental steps. Baselines instead oscillate near the boundary (Fig. 5, p.8 [VI]). The authors conclude that "effective safety failure does not require gradual erosion" [p.8]. Named entities from role initialization act as "representational anchors," producing abrupt rather than gradual transitions [p.9; App. A p.12–13]. |
| **Limitations** | Stated by the authors (App. H, p.18): the framework does not enumerate all trajectories or capture the full internal dynamics; future work includes longer horizons, multimodal settings, and defensive monitoring. *Interpretation / observed:* (a) X-Teaming numbers for models other than Llama-3-8B are copied from the original work, not reproduced [p.5]; (b) there is one judge (GPT-4o) and no human agreement is reported in the provided copy; (c) white-box analysis covers one model; (d) **Fig. 4 disagrees with the text** (see below); (e) **Figs. 6–7 mix up "Alignment Score" and "mutual information"** (see below); (f) there is no benign-conversation control. |
| **Deployment constraints** | Not addressed. The paper studies attacks. |
| **Relevance to EcomSafe** | High for **RQ1** (hidden-state change across turns) and for the design of the trajectory features. Its evidence of *abrupt*, early boundary crossing directly challenges any detector whose main signal is gradual trend (Kendall's τ, running mean). Its own e-commerce-adjacent example is "fabricated customer reviews on Amazon" (Fig. 6 caption, p.12). Its judge policy lists "Fraudulent or deceptive activity" (App. D, p.15). |

#### 1.3.1 SDSF key quantitative results
| Result | Value | Source |
|---|---|---|
| SFR on HarmBench, STAR (GPT-4o / Claude 3.5 / Gemini 2.0-F / Llama-3-8B / Llama-3-70B) | 94.5 / 74.0 / 96.1 / 89.0 / **85.5** | Table 1, p.6 [VI: the 85.5 corrects the OCR's "$5.5"] |
| Best single-turn baseline (CodeAttack) | 70.5 / 39.5 / – / 46.0 / 66.0 | Table 1, p.6 |
| X-Teaming | 94.3 / 67.9 / 87.4 / 85.5 / 84.9 | Table 1, p.6 |
| ActorAttack | 84.5 / 66.5 / 42.1 / 79.0 / 85.0 | Table 1, p.6 |
| Crescendo | 46.0 / 50.0 / – / 60.0 / 62.0 | Table 1, p.6 |
| STAR vs X-Teaming on Gemini | +8.7 pp | p.6 (consistent with Table 1) |
| Auxiliary temperature 0.2 / 0.7 / 1.0 | SFR 88.0 / 89.0 / 88.0 | Table 2, p.6 |
| JailbreakBench (Llama-3-8B / GPT-4o / Gemini), avg token cost | STAR 94.0 / 96 / 100 at 29K; X-Teaming 85.5 / 94 / 86 at 37K; ActorAttack 37.5 / 46 / 42 at 15K | Table 3, p.6 |
| Ablation, drop in SFR (JailbreakBench, Llama-3-8B-IT) | History accumulation −25.5; adaptive retry −19.7; role init −17.8; state feedback −14.7; prompt softening −11.6 | Fig. 2, p.7 [VI]; text p.7 |
| History causality (mean judge score, original = 5.00) | Shuffle 4.11; truncate 50% 3.92; truncate 30% 3.62; keep last 2 3.26; keep last 1 3.56; refusal inserted at beginning 3.96, middle 3.98, end 3.72; initial scene replaced by refusal 3.60 | Fig. 3, p.7 [VI] |
| Auxiliary model scale (Qwen 32B vs 7B at temps 0.2 / 0.7 / 1.0) | 88/89/88% vs 84/88/82% | Table 4, p.15 |
| Refusal-direction projection | The text [p.8] says "final-layer" values of 2.35 (original) → 0.13 (T1) → 0.08 (T2) → −0.0081 (T3). **The Fig. 4 plot [VI] shows these values near layer ~12, not at the final layer.** At the final layer the plot shows Original ≈5.2, T1 ≈2.1, T2 ≈−0.6, T3 ≈1.25, X-Teaming ≈−0.2, ActorAttack ≈−1.9. That is non-monotonic, and the baselines sit *below* STAR, contrary to the text. | Fig. 4, p.8 |
| Token-level alignment score by turn | Mean AS 0.147 (J=1), 0.208 (J=3), 0.282 (J=5); peaks at the persona token "Amelia" | Fig. 6, p.12 [VI] |

*Safe use (interpretation):* cite Fig. 4 only as "refusal-direction projection is suppressed around layer 12 under STAR relative to the original prompt," and state the text/figure inconsistency. Cite Figs. 6–7 as an "alignment/MI proxy," not as verified mutual information: the axes are labelled "Alignment Score," the captions say "mutual information," and Fig. 7's "Mean MI = 0.282" equals Turn 3's mean AS.

---

### 1.4 Target: EcomSafe (Cart Before the Harm), summarized for comparison
Koshal & Sushmita, Northeastern University (Koshal also Meta), May 29, 2026 [EcomSafe p.1]. *Note:* the title on page 1 reads "Multi-Turn Safety Detection…," but the original file name reads "Real-Time Safety Detection…".

- **Problem:** per-turn guardrails in shopping agents miss multi-turn escalation and commercial (business-rule) jailbreaks [p.1].
- **RQ1–RQ5** [p.1]: RQ1, hidden-state change under commercial multi-turn jailbreaks; RQ2, whether a trajectory model can detect what single-turn filters miss; RQ3, the most predictive features; RQ4, variation by threat class and domain; RQ5, per-turn latency.
- **Threats** [p.2]: TC1, single-turn commercial jailbreaks (price manipulation, policy bypass, return fraud, competitor extraction, regulatory bypass; Table 1). TC2, multi-turn escalation (linear, camouflaged, late spike). TC3, coordinated cross-user attacks.
- **Architecture** [p.2–3]: (1) a per-turn hidden-state probe over the intents PV/CD/FF/RB/CR, combined as r_t = p_FF + 0.8·p_RB + 0.6·p_PV + 0.4·p_CD (Eq. 1). (2) An incremental trajectory model TR(x_{1:t}) = σ(f_θ(r_1…r_t, Δ_t, μ_t, σ_t, τ_t)) (Eq. 2), with an intervention if TR > θ_traj **or** r_t > θ_local.
- **EcomSafeBench** [p.3]: 3,900 conversations in 5 domains: 1,300 commercial jailbreaks, 1,100 multi-turn escalations, 1,500 benign.
- **Models** [p.3]: Llama-3.2-3B-Instruct and Llama-3.1-8B.
- **Baselines** [p.3]: isolated per-turn classifiers, output filters, keyword filters, sliding-window max-risk, full-context models.
- **Metrics** [p.3]: ROC AUC per class; early-detection rate (caught before turn 5); FPR on benign; per-turn latency.

---

## 2. Thematic synthesis

### 2.1 Why single-turn safety evaluation fails
**Source claims.** All three prior works reject message-level evaluation, but they give different kinds of evidence.
- **Behavioral evidence (PSB).** Two defenders that are statistically indistinguishable at T1 (34.8% vs 31.8%, p = .43) end up 19× apart by T4 under the same attacker (Table 4, p.4; Fig. 3, p.5). The authors conclude that single-turn benchmarks give "an incomplete and potentially misleading signal for deployment decisions" [PSB p.6].
- **Attack-success evidence (SDSF).** Models that look robust to single-turn attacks (e.g., Claude 3.5 Sonnet at 3.0% under GCG and PAIR) reach 74.0% SFR under STAR (Table 1, p.6). The authors read this as evidence that safety alignment "is not governed by a fixed decision boundary" but is "strongly state-dependent" [SDSF p.6].
- **Architectural argument (CF).** Deployed guard classifiers (Llama Guard, ShieldGemma, WildGuard, Granite Guardian, the OpenAI moderation classifier, Constitutional Classifiers) "all judge each message in isolation" [CF p.2, 2nd]. The paper also cites reports that multi-turn human red-teamers exceed 70% attack success on HarmBench against defenses whose single-turn success is in the single digits [CF p.2, 2nd].

**Interpretation.** The papers converge on the claim, but the causes they give differ. PSB points to user *pressure tactics* (urgency, authority, emotion). SDSF points to *autoregressive self-conditioning* on the model's own prior compliant outputs. CF points to the *absence of intent, memory, and authority verification* in the guard. EcomSafe's motivation [p.1] names only the "evaluate user inputs in isolation" cause. The prior work suggests at least two more mechanisms that an e-commerce detector should represent: the agent's own responses as state (SDSF), and asserted authority (CF, PSB).

### 2.2 Multi-turn escalation and conversational risk accumulation
**Source claims.**
- *Where and how fast risk accumulates.* In PSB, the live attack jumps from 34.8% to 77.7% at T2 and then plateaus (Table 2, p.3; Fig. 1, p.4). Turn 2 is called the critical window [PSB p.4]. In SDSF, STAR's first interaction turn produces a "large displacement" into the compliance region, and effective failure "does not require gradual erosion" (Fig. 5, p.8).
- *What drives accumulation.* In PSB, adaptive tactic *selection* matters more than rewording: there is a 19.1 pp gap between template-adaptive and live attacks [PSB p.3]. The most dangerous combination is emergency framing plus an authority claim [PSB p.3–4]. In SDSF, removing history accumulation causes the largest ablation drop, −25.5 (Fig. 2, p.7). Order matters: shuffling alone drops the score from 5.00 to 4.11 (Fig. 3, p.7).
- *Model-dependent trajectories.* PSB's four signatures (compliance creep, diminishing returns, pattern recognition, spike-and-abandonment) show that the *same* attacker produces opposite trajectories on different defenders [PSB p.4–5]. The same model can also become more *resistant* over turns: Claude names the manipulation pattern in 0.9% of T1 responses and 38.8% of T4 responses [PSB p.4].
- *Decomposition.* CF describes attacks that split a forbidden objective into benign sub-questions (ActorAttack [2nd]) or escalate using the model's own replies (Crescendo [2nd]) [CF p.1–2].

**Interpretation.** EcomSafe's TC2 taxonomy (linear, camouflaged, late spike [p.2]) is framed around the *user-side risk profile*. The prior evidence suggests that the most consequential empirical pattern is an **early step change**: PSB at T2, SDSF at the first turn after initialization. That pattern fits "late spike" only loosely and "linear" poorly. Neither prior paper studies EcomSafe's "camouflaged escalation" (interleaved benign turns) directly. SDSF's shuffle and truncation perturbations (Fig. 3) are the closest related evidence. They suggest that *order* and *early context-setting* carry signal: keeping only the last 2 scenes (3.26) produced lower compliance than keeping only the last one (3.56).

### 2.3 State-dependent / trajectory-based safety modeling
**Source claims.**
- SDSF formalizes safety as operating over a latent state z_t, with history 𝓗_t as its observable proxy [SDSF p.3]. It reports white-box evidence on Llama-3-8B-IT that the refusal-direction projection is suppressed under STAR, and that latent states cross into a compliance region (Figs. 4–5, p.8). These are caveated in §1.3.1.
- PSB models trajectories only *behaviorally* (judge scores per turn) and argues that "trajectory shapes may reveal mechanisms, not just endpoints" [PSB p.6].
- CF's Table I lists four existing defenses with trajectory analysis (TurnGate, THRD, CivicShield, TCA; blank = present) [CF p.2, VI, 2nd]. It describes THRD as fusing per-turn risk with historical context into "one time-decayed composite" and criticizes such approaches for reducing the conversation "to a single score" [CF p.2].

**Interpretation.**
- EcomSafe's hidden-state probe (RQ1) is supported *in principle* by SDSF's evidence that internal representations shift across turns on a Llama-3-8B-class model. EcomSafe also targets Llama-3.1-8B [EcomSafe p.3]. However, SDSF's representational evidence is thinner than its text suggests (the Fig. 4 inconsistency; the AS/MI mix-up), comes from one model, and was gathered on attack trajectories without benign controls.
- EcomSafe's trajectory features (Δ_t, μ_t, σ_t, τ_t) are summary statistics of a *scalar* per-turn risk. SDSF argues that the failure signal is *multi-dimensional*: refusal suppression plus role-conditioned coupling [p.9]. CF argues that single-score reduction is itself a weakness [p.2]. EcomSafe's f_θ(·) takes the whole sequence r_1…r_t, which may partly offset this, but it still sees only scalar per-turn scores and no per-intent vector.
- A time-decayed per-turn-risk composite over history (THRD, as described secondhand in CF p.2) is conceptually close to EcomSafe's incremental trajectory layer. What that system actually contains cannot be verified from the provided material.

### 2.4 Classifier-based defenses
**Source claims.**
- PSB is the only prior paper with a *measured* classifier defense. A six-way category classifier is accurate on single turns: 93.3% (Claude) and 82.3% (GPT) (Table 6, p.6). Under adversarial history, its accuracy falls from 95.5% to 48.5% (Table 8, p.7). "The failure mode is not increased missed detection… but lateral category confusion" (3.7 → 50.0%) [PSB p.6]. Lateral errors converge on Unlicensed Practice (55 → 71% of lateral errors, Fig. 5, p.7). Even so, the input-side tag cut the T4 unsafe rate by 52.2 pp, because "a partial signal halved the harm" [PSB p.6].
- CF argues that the classifier framing is "why a patient adversary can still extract restricted content," and that guarding is "a comprehension problem" [CF p.1]. Its own measured comparison against guard models is **[NV]**.

**Interpretation.**
- PSB's lateral-drift result bears directly on EcomSafe Eq. 1. EcomSafe maps per-intent probabilities to a scalar with **fixed, unequal weights** (FF 1.0, RB 0.8, PV 0.6, CD 0.4 [p.2]). If adversarial history causes probability mass to move *between* harmful intents, as PSB saw between harmful categories, then r_t will change even when total harmfulness does not. In EcomSafe's scheme, drift from FF to CD would *lower* the score by 60%. *Implication:* EcomSafe should report whether the probe's per-intent predictions drift across turns (a PSB-style Phase-2 analysis), and should ablate the weighting against a max or sum over harmful intents.
- PSB's classifier reads text through an LLM prompt; EcomSafe's reads hidden states [EcomSafe p.2]. No provided paper tests whether hidden-state probes resist PSB-style lateral drift any better. This is an open empirical question, not a demonstrated advantage.
- The CR (Compliant Refusal) intent receives no weight in Eq. 1 [EcomSafe p.2]. SDSF shows that refusals in history *protect* the model (inserting a refusal lowered the score to 3.60–3.98, Fig. 3, p.7), and PSB shows Claude's growing recognition of manipulation [p.4]. A refusal signal may therefore be informative *as a trajectory feature*, for example to detect an attacker pushing past refusals. EcomSafe does not use it that way.

### 2.5 Proactive / session-level guardrails
**Source claims.**
- CF is the only paper proposing a session-level, pre-generation guard: an independent oversight model, blocking before generation, escalation-based combination, and auditable rationales [CF p.1–2]. Its efficacy numbers are **[NV]**.
- PSB's intervention acts per turn on the input and does not block; it recommends that "future systems should combine input classification with output-side review, uncertainty-aware escalation, and conversation-level pattern detection" [PSB p.6].
- SDSF proposes, but does not build, early interception plus joint-signal monitoring [SDSF p.9].

**Interpretation.**
- EcomSafe's rule "TR > θ_traj **or** r_t > θ_local" [p.3] is an escalation-style OR over two layers. That matches CF's argued preference for escalation over averaging [CF p.1–2]. *Within* the per-turn layer, however, Eq. 1 is a weighted sum, which is the kind of score averaging CF argues dilutes confident signals.
- EcomSafe's interventions (block the response, flag the session, escalate to a human [p.3]) are session-level. The proposal does not specify whether the probe reads hidden states *before* the agent generates (on the user turn) or *after* (on the response). CF distinguishes these as pre-generation and output gates [CF p.1]. The choice decides whether EcomSafe can prevent harm or only detect it.
- None of the three prior works addresses EcomSafe's **TC3 (coordinated cross-user attacks)**. The EcomSafe architecture as described is per-session (Eq. 2 is indexed by the turns of one dialogue), so TC3 is unaddressed within the proposal itself.

### 2.6 Early detection of escalation
**Source claims.**
- PSB: Turn 2 is the "critical vulnerability window," and "targeted Turn 2 hardening may have outsized impact," though this "would need validation in deployment conditions" [PSB p.6]. The 4-turn benchmark limits observable horizons [PSB p.7].
- SDSF: "professionally framed personas combined with semantically softened queries in the first one to two turns constitute a detectable initialization signature" [SDSF p.9]. Removing role initialization alone drops SFR by 17.8 (Fig. 2, p.7).
- CF: TurnGate "blocks at the earliest harm-enabling turn" [CF p.2, 2nd].

**Interpretation.**
- EcomSafe's metric "percentage of multi-turn attacks caught before turn 5" [p.3] may be too loose given this evidence. PSB's dialogues end at turn 4, and the harm step occurs at T2. SDSF crosses the boundary in the first STAR turn, with T_max=7. A detector that fires at turn 4 would count as "early" under EcomSafe's metric but would arrive *after* the harmful response in the PSB and SDSF regimes. *Suggested alternative (interpretation):* report detection lead time relative to the *first harmful-response turn*, which requires turn-level harm labels in EcomSafeBench.
- Kendall's τ over turn index and a running mean μ_t both need several turns before they are informative. On abrupt 1–2-turn transitions, only r_t > θ_local and Δ_t can respond in time. Ablations should therefore show what each trajectory feature adds *by turn index*.

### 2.7 False-positive and deployment tradeoffs
**Source claims.**
- PSB gives the only measured false-alarm data. On 100 XSTest benign prompts: 45% (GPT classifier) and 16% (Claude classifier) (Table 6, p.6). "Nearly half of safe patient queries would be incorrectly flagged"; even 16% means "one in six" [PSB p.6]. The authors call this the *primary* deployment constraint [PSB p.1, p.6].
- CF reports 8% over-refusal in its abstract [CF p.1, **NV**].
- SDSF warns that benign multi-turn interactions "naturally occupy low refusal-activation regions," so a refusal-projection threshold alone would misfire [SDSF p.9]. No benign measurement is given.
- Evaluation-pipeline pitfalls: PSB's judge sees only the current turn and "cannot score multi-turn escalation patterns directly" [PSB p.7]. Safety-trained attackers self-limit, and unhandled attacker refusals "inflate apparent safety" [PSB p.5, p.7]. SDSF uses a helpful-only auxiliary model partly to avoid this [SDSF p.5].
- **Latency**: none of the three prior papers reports runtime or latency. SDSF reports attacker *token cost* (Table 3, p.6), which is not defender latency.

**Interpretation.**
- EcomSafe's FPR set is "multi-turn customer service and shopping dialogues" [p.3]. PSB's result suggests that the hard cases are *borderline-benign* queries that look like attacks: legitimate returns of defective items, honest price-match requests, pharmacist-style dosage questions. A generic benign set may understate FPR. XSTest played this role in PSB [PSB p.2].
- EcomSafe's RQ5 (latency) has no counterpart in the provided prior work, which makes it a potentially distinctive but *unbenchmarked* contribution.
- Class balance: EcomSafeBench is 2,400 attacks to 1,500 benign [p.3]. Deployment traffic is overwhelmingly benign, so ROC AUC alone will not reflect the operating-point cost that PSB emphasizes. FPR at fixed recall (or the reverse) is needed.

### 2.8 Remaining research gaps (as evidenced by the provided sources)
1. **No commercial or business-rule threat taxonomy** exists in the provided prior work. PSB is medical [p.1–2]. SDSF uses HarmBench and JailbreakBench [p.5]. CF's benchmarks are **[NV]**. EcomSafe's TC1 taxonomy (Table 1, p.2) addresses this gap. *Caveat:* SDSF's Fig. 6 example (fake Amazon reviews, p.12) and its judge policy's "Fraudulent or deceptive activity" (p.15) show that some commerce-related harms already appear inside general benchmarks.
2. **No measured hidden-state *detector* over multi-turn trajectories** exists in the provided works. SDSF analyzes representations but builds no detector [p.9]. PSB's classifier works on text [p.3]. CF's gates are LLM-judgment-based, as far as the copy shows [p.1].
3. **No benign-trajectory controls for representational signals.** SDSF asserts separability from benign interactions without showing it [p.9].
4. **No latency or cost evaluation of defenses.**
5. **No cross-session or cross-user attack study.**
6. **Evaluation-infrastructure gaps.** There is no judge that scores whole conversations (PSB p.7), and generating attack data with safety-trained LLMs is itself unreliable (PSB p.5).
7. **Authority-claim handling.** Authority is central in CF (zero-trust gate) [p.1], PSB (the two-element formula) [p.3–4], and SDSF (personas) [p.4]. It is absent from EcomSafe's feature set, even though EcomSafe's own Regulatory Bypass example uses one ("I'm a nurse") [p.2].

---

## 3. EcomSafe vs prior work (summary)
Detailed tables are in `comparison_table.md`. The full overlap, novelty-risk, and experiment analysis is in `gap_analysis.md`. In brief (interpretation):

- **Direct overlap:** the multi-turn escalation motivation (all three); the per-turn category classifier as a safety signal (PSB); hidden-state change across turns (SDSF); session-level blocking with escalation logic (CF); trajectory-aware per-turn-risk aggregation (THRD and TurnGate as described in CF, 2nd).
- **What is plausibly distinctive:** the commercial threat taxonomy and the EcomSafeBench domains; a *hidden-state probe* feeding an *incremental* trajectory model; explicit trajectory statistics (Δ, μ, σ, τ); latency measurement.
- **Most at-risk claim:** the implication that existing guardrails lack trajectory tracking [EcomSafe p.1]. The CF copy itself lists four trajectory-aware defenses [CF p.2].

---

## 4. Reference list (provided sources only)
- **[EcomSafe]** J. Koshal, S. Sushmita. "Cart Before the Harm: Multi-Turn Safety Detection in E-Commerce Conversational Agents." Proposal, Northeastern University, May 29, 2026. (`papers/ocr/cart_before_the_harm_ocr.pdf`, 3 pp.)
- **[CF]** M. Guida et al. "Cognitive Firewall: A Proactive, Zero-Trust, Multi-Gate Framework for LLM Safety." arXiv:2607.01277v1, 2026. (`papers/ocr/cognitive_firewall_ocr.pdf`, 2 pp.; **incomplete copy**)
- **[PSB]** [A]nushka Sheoran, Y. Hao. "MultiTurnPSB: Evaluating Multi-Turn Jailbreak Attacks and Classifier-Based Defenses for Medical AI Safety." arXiv:2606.02630v1, 2026. (`papers/ocr/multiturn_psb_ocr.pdf`, 9 pp.)
- **[SDSF]** P. Li et al. "State-Dependent Safety Failures in Multi-Turn Language Model Interaction." ICML 2026, PMLR 306; arXiv:2603.15684v2. (`papers/ocr/state_dependent_safety_failures_ocr.pdf`, 18 pp.)
