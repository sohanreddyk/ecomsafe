## Background and Related Work

We review five verified peer-reviewed papers (§2.1), note additional non-core work (§2.2), synthesize themes (§2.3), and position EcomSafe (§2.4). Core titles and venues were checked against official proceedings pages.

### 2.1 Peer-reviewed core

**[CRES] Russinovich, Salem, and Eldan. "Great, Now Write an Article About That: The Crescendo Multi-Turn LLM Jailbreak Attack." USENIX Security Symposium, 2025.**
*Scope:* The paper introduces Crescendo, a multi-turn jailbreak that opens with benign, abstract questions related to a target task. It then escalates gradually until the model produces content it would refuse if asked directly.
*Methodology:* The authors run Crescendo manually against ChatGPT, Gemini Pro, and LLaMA variants. They then automate it as Crescendomation, which outperforms prior jailbreaks on an AdvBench subset by 29–61% on GPT-4 and 49–71% on Gemini-Pro.
*Critical Takeaway:* Because each turn looks benign on its own, gradual escalation is hard for per-message filters to detect, even once the attack pattern is known.

**[ACTB] Ren et al. "LLMs know their vulnerabilities: Uncover Safety Gaps through Natural Distribution Shifts." Proceedings of the 63rd Annual Meeting of the ACL (Volume 1: Long Papers), 2025.**
*Scope:* The paper studies how shifting a harmful request toward semantically related but innocuous-looking topics can expose safety gaps in aligned LLMs across multiple turns.
*Methodology:* The proposed attack, ActorBreaker, draws on actor-network theory. It identifies "actors" (people, objects, concepts) linked to a harmful target and chains queries about them toward that target. The authors also build a multi-turn safety dataset for fine-tuning defenses.
*Critical Takeaway:* An attack can reach a harmful target through related concepts rather than explicit phrasing, so defenses keyed to that phrasing miss it.

**[HB] Mazeika et al. "HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal." ICML 2024 (PMLR 235).**
*Scope:* HarmBench is a standardized framework for evaluating automated red-teaming attacks and the robustness of LLM refusals.
*Methodology:* The authors specify desirable properties for red-teaming evaluation and build a behavior set and scoring pipeline that meet them. They use it to compare 18 red-teaming methods against 33 target LLMs and defenses, and they propose an efficient adversarial-training defense.
*Critical Takeaway:* Attack success rates cannot be compared across papers without a shared threat model, behavior set, and judge.

**[JBB] Chao et al. "JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models." NeurIPS 2024, Datasets and Benchmarks Track.**
*Scope:* JailbreakBench addresses inconsistent and irreproducible jailbreak evaluation with an open benchmark.
*Methodology:* The benchmark provides an evolving repository of jailbreak artifacts, a dataset of 100 misuse behaviors, a standardized evaluation framework with a defined threat model and scoring, and a public leaderboard.
*Critical Takeaway:* Jailbreak results are credible only when prompts, code, and scoring are released for others to reproduce.

**[REF] Arditi et al. "Refusal in Language Models Is Mediated by a Single Direction." NeurIPS 2024, Main Conference Track.**
*Scope:* The paper shows that refusal in open-source chat models is mediated by a single residual-stream direction. Removing this direction disables refusal, and adding it induces refusal on harmless prompts.
*Methodology:* The direction is extracted as the difference in mean activations between harmful and harmless instructions and tested causally through directional ablation and activation addition. A rank-one weight edit based on it yields a white-box jailbreak.
*Critical Takeaway:* Safety behavior is concentrated in a low-dimensional, fragile internal structure, which makes it easy to remove and also readable by probes.

### 2.2 Additional preprint and non-core work

These works inform our design but are **not counted**, because none has a confirmed peer-reviewed venue.
- **Cognitive Firewall [CF]** (Guida et al., arXiv:2607.01277). It proposes session-level oversight through four categorical gates. Our partial copy leaves its method and results [NV].
- **MultiTurnPSB [PSB]** (Sheoran and Hao, arXiv:2606.02630). It evaluates multi-turn attacks and a per-turn classifier defense in the medical domain.
- **State-Dependent Safety Failures [SDSF]** (Li et al.). It is listed as ICML 2026 in our notes, but we have not verified this on an official page.
- **Speak Out of Turn [SOT]** (Zhou et al., arXiv:2402.17262). It decomposes harmful requests into multi-turn sub-queries. We found no peer-reviewed venue for it.

### 2.3 Thematic synthesis

**Single-turn evaluation understates conversational risk.** Among the works reviewed here, core and non-core papers alike find message-level evaluation misleading.
- **Core evidence.** Crescendo shows that escalation built from individually benign turns defeats commercial models [CRES]. ActorBreaker reaches harmful targets without explicit harmful phrasing [ACTB].
- **Additional evidence.** Sheoran and Hao report two defenders indistinguishable at the first turn (34.8% vs. 31.8% unsafe) but diverge by the fourth [PSB]. Li et al. report that Claude 3.5 Sonnet succumbs to 3.0% of GCG and PAIR attacks but 74.0% of multi-turn STAR trajectories [SDSF]. Guida et al. note that deployed guard classifiers judge each message in isolation [CF].

**Escalation takes several shapes:**
- *Gradual escalation:* Crescendo raises the stakes step by step [CRES].
- *Indirect approach:* ActorBreaker approaches the target through related actors [ACTB].
- *Decomposition:* Speak Out of Turn splits a request so that no single reply is objectionable [SOT].
- *Early step change:* non-core evidence suggests risk often jumps early. Sheoran and Hao identify Turn 2 as a "critical vulnerability window" [PSB], and Li et al. conclude that failure "does not require gradual erosion" [SDSF].

An escalation taxonomy should therefore cover early step changes alongside linear, camouflaged, and late-spike patterns. Among the works reviewed here, none studies camouflaged escalation in isolation.

**Internal representations carry safety-relevant signal.** Arditi et al. establish that refusal is mediated by a readable direction [REF]. This motivates hidden-state probes, though a white-box adversary could suppress that signal. Li et al. report suppressed refusal-direction projections across turns, but only on a single model and for attack trajectories, so we treat this as motivating rather than conclusive [SDSF]. Among the works reviewed here, none tests whether hidden-state probes resist lateral drift better than text classifiers, and we make no such claim.

**Evaluation must be standardized and reproducible.** HarmBench and JailbreakBench argue that results need a fixed threat model, behavior set, and judge, plus released artifacts [HB; JBB]. Non-core work adds that current-turn-only judges cannot score escalation, and that false-alarm rates of 16–45% on benign prompts are the primary deployment constraint for classifier defenses [PSB].

**Trajectory-aware defenses already exist.** Guida et al. list TurnGate, THRD, CivicShield, and TCA as trajectory-aware defenses, though these descriptions are secondhand [CF]. Tracking risk across turns is therefore not new, and EcomSafe belongs to this family.

### 2.4 Positioning EcomSafe

Among the works reviewed here, none targets business-logic violations in e-commerce agents. Fraud-adjacent harms such as fake reviews appear inside general benchmarks, but without a commercial taxonomy [SDSF]. EcomSafe addresses part of this space with five contributions:
1. **Commercial threat modeling.** Harm is defined as a violated business rule in shopping agents, not only as harmful content.
2. **A commercial jailbreak taxonomy.** Price manipulation, policy bypass, return fraud, competitor extraction, and regulatory bypass, in both single-turn and multi-turn forms. This is a systematic taxonomy and benchmark, not the first appearance of these harms.
3. **Trajectory features for commercial attacks.** Escalation delta, running mean, volatility, and rank trend, computed over a hidden-state intent probe. Whether they add signal beyond existing trajectory-aware aggregators is for our ablations to test.
4. **Early detection.** Measured as lead time before the first harmful response, since prior evidence places the decisive window early [PSB; SDSF].
5. **Product-domain evaluation.** Results by attack class and product domain against trajectory-aware baselines, with false-positive rates on borderline-benign shopping dialogues and per-turn latency.

Cross-user coordinated attacks remain outside the current architecture.

---
*Citation keys:* [CRES], [ACTB], [HB], [JBB], and [REF] are the verified peer-reviewed core. [CF], [PSB], [SDSF], and [SOT] are non-core and not counted. [NV] marks a claim not verifiable from our copy.
