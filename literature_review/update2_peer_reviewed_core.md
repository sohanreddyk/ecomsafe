# Update 2: peer-reviewed core (10 papers, plus 2 alternates)

**Course requirement:** a complete review of at least 10 peer-reviewed conference papers. Each paper needs Scope (1–2 sentences), Methodology (1–2 sentences) and a Critical Takeaway (1 sentence).

**Verification rule:**
- A paper counts only if its venue was confirmed on an official proceedings page: ACL Anthology, proceedings.neurips.cc, PMLR, proceedings.iclr.cc, usenix.org.
- arXiv-only work never counts.

**Verification dates:**
- Papers 2, 3, 4, 5 and 6 were verified on 2026-09-27 for Update 1 (see `peer_reviewed_core.md`).
- Every other entry was verified on 2026-10-18 by opening the official page listed.
- OpenReview blocked automated access, so ICLR 2025 papers were verified on proceedings.iclr.cc.

**Selection:** papers were chosen for how directly they bear on the staged problem:
- **Phase 1 (now):** a policy-grounded single-turn benchmark with matched negatives, boundary cases, a blind judge and a lexical shortcut audit.
- **Phase 2:** per-turn and representation-level detection.
- **Phase 3:** multi-turn trajectories.

## Summary

| # | Paper | Venue | Main role for EcomSafe |
|---|---|---|---|
| 1 | Nakash et al., Effective Red-Teaming of Policy-Adherent Agents | EMNLP 2025 (main) | Policy-adherent agent attacks (closest prior work) |
| 2 | Mazeika et al., HarmBench | ICML 2024 (PMLR 235) | Standardized red-teaming evaluation |
| 3 | Chao et al., JailbreakBench | NeurIPS 2024, Datasets & Benchmarks | Reproducible jailbreak benchmark |
| 4 | Russinovich et al., Crescendo | USENIX Security 2025 | Multi-turn escalation (Phase 3) |
| 5 | Ren et al., LLMs know their vulnerabilities (ActorBreaker) | ACL 2025 (Long) | Indirect multi-turn attacks (Phase 3) |
| 6 | Arditi et al., Refusal Is Mediated by a Single Direction | NeurIPS 2024 (main) | Representation-level signal (Phase 2) |
| 7 | Yao et al., τ-bench | ICLR 2025 | Policy-bound retail agents |
| 8 | Jiang et al., WildTeaming at Scale | NeurIPS 2024 (main) | Contrastive benign counterparts that look harmful in form |
| 9 | Röttger et al., XSTest | NAACL 2024 (Long) | Boundary cases and over-refusal |
| 10 | Gururangan et al., Annotation Artifacts in NLI Data | NAACL 2018 (Short) | Lexical shortcuts and dataset artifacts |
| Alt-A | Zhang et al., JBShield | USENIX Security 2025 | Hidden-state jailbreak detection (Phase 2) |
| Alt-B | Gardner et al., Contrast Sets | Findings of EMNLP 2020 | Minimal-pair evaluation |

How the set covers the required themes:

| Theme | Papers |
|---|---|
| Policy-adherent agent attacks and commercial policy violations | 1, 7 |
| Benchmark construction and evaluation reproducibility | 2, 3, 7 |
| Hard or benign counterparts and boundary cases | 8, 9 (Alt-B) |
| Red teaming | 1, 2, 8 |
| Shortcuts and dataset artifacts | 10 (Alt-B) |
| Hidden-state or representation-level detection | 6 (Alt-A) |
| Multi-turn attacks | 4, 5 |

---

## 1. Effective Red-Teaming of Policy-Adherent Agents

- **Authors:** Itay Nakash, George Kour, Koren Lazar, Matan Vetzler, Guy Uziel, Ateret Anaby Tavor
- **Venue:** Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing (EMNLP 2025, main conference), pp. 2250–2268
- **Year:** 2025
- **DOI / ID:** 10.18653/v1/2025.emnlp-main.114 (Anthology ID 2025.emnlp-main.114)
- **Official URL:** https://aclanthology.org/2025.emnlp-main.114/
- **Status:** verified; the main conference, not Findings. The preprint is arXiv 2506.09600.
- **Why it matters:**
  - It is the closest prior work: adversarial customers who try to make a customer-service agent break its policy (for example refunds or cancellations) for their own benefit.
  - Several EcomSafe framing techniques follow its policy-aware persuasion strategies.
  - Unlike EcomSafe, it red-teams agents in multi-turn interaction. It does not build matched legitimate negatives or measure lexical separability.
- **Scope (draft):** The paper studies agents that must follow strict policies, such as refund or cancellation rules, against users who try to manipulate them into violating those policies for personal gain.
- **Methodology (draft):** The authors propose CRAFT, a multi-agent red-teaming system that uses policy-aware persuasion strategies, and introduce tau-break, a benchmark built on τ-bench for measuring agent robustness to manipulation. They compare CRAFT with conventional jailbreak methods and evaluate simple defenses.
- **Critical Takeaway (draft):** Policy-aware persuasion breaks policy-adherent agents more effectively than generic jailbreaks and the simple defenses tested are insufficient, so commercial-policy violations need their own evaluation.

## 2. HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal

- **Authors:** Mantas Mazeika, Long Phan, Xuwang Yin, Andy Zou, Zifan Wang, Norman Mu, Elham Sakhaee, Nathaniel Li, Steven Basart, Bo Li, David Forsyth, Dan Hendrycks
- **Venue:** Proceedings of the 41st International Conference on Machine Learning (ICML 2024), PMLR 235, pp. 35181–35224
- **Year:** 2024
- **DOI / ID:** none issued (PMLR)
- **Official URL:** https://proceedings.mlr.press/v235/mazeika24a.html
- **Status:** verified (Update 1)
- **Why it matters:**
  - It is the model for EcomSafeBench's fixed threat model, behavior set and judge.
  - It defines harm as objectionable content, which is exactly the gap where commercial rule violations fall through.
- **Scope (draft):** HarmBench is a standardized framework for evaluating automated red-teaming attacks and the robustness of LLM refusals.
- **Methodology (draft):** The authors specify the properties a red-teaming evaluation needs and build a behavior set and scoring pipeline that meet them. They use it to compare 18 red-teaming methods against 33 target LLMs and defenses, and propose an efficient adversarial-training defense.
- **Critical Takeaway (draft):** Attack success rates cannot be compared across papers without a shared threat model, behavior set and judge.

## 3. JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models

- **Authors:** Patrick Chao, Edoardo Debenedetti, Alexander Robey, Maksym Andriushchenko, Francesco Croce, Vikash Sehwag, Edgar Dobriban, Nicolas Flammarion, George J. Pappas, Florian Tramèr, Hamed Hassani, Eric Wong
- **Venue:** Advances in Neural Information Processing Systems 37 (NeurIPS 2024), Datasets and Benchmarks Track, pp. 55005–55029
- **Year:** 2024
- **DOI / ID:** 10.52202/079017-1745
- **Official URL:** https://proceedings.neurips.cc/paper_files/paper/2024/hash/63092d79154adebd7305dfd498cbff70-Abstract-Datasets_and_Benchmarks_Track.html
- **Status:** verified (Update 1; re-confirmed 2026-10-18)
- **Why it matters:** It motivates releasing EcomSafeBench's generation code, prompt templates, configs and per-stage rejection logs, so that both the dataset and its quality diagnostics can be reproduced.
- **Scope (draft):** JailbreakBench addresses inconsistent and irreproducible jailbreak evaluation with an open benchmark.
- **Methodology (draft):** The benchmark provides an evolving repository of jailbreak artifacts, a dataset of 100 misuse behaviors, a standardized evaluation framework with a defined threat model and scoring, and a public leaderboard.
- **Critical Takeaway (draft):** Jailbreak results are credible only when prompts, code and scoring are released for others to reproduce.

## 4. Great, Now Write an Article About That: The Crescendo Multi-Turn LLM Jailbreak Attack

- **Authors:** Mark Russinovich, Ahmed Salem, Ronen Eldan
- **Venue:** 34th USENIX Security Symposium (USENIX Security 25), pp. 2421–2440
- **Year:** 2025
- **DOI / ID:** none issued (USENIX)
- **Official URL:** https://www.usenix.org/conference/usenixsecurity25/presentation/russinovich
- **Status:** verified (Update 1; re-confirmed 2026-10-18)
- **Why it matters:**
  - It is the canonical gradual-escalation attack, and it motivates Phase 3 and the linear-escalation pattern.
  - It also explains why EcomSafe has to scope Phase 1 explicitly to single-turn attacks.
- **Scope (draft):** The paper introduces Crescendo, a multi-turn jailbreak that opens with benign, abstract questions about a target task and escalates gradually until the model produces content it would refuse if asked directly.
- **Methodology (draft):** The authors run Crescendo manually against ChatGPT, Gemini Pro and LLaMA variants. They then automate it as Crescendomation, which beats prior jailbreaks on an AdvBench subset by 29–61% on GPT-4 and 49–71% on Gemini-Pro.
- **Critical Takeaway (draft):** Each turn looks benign on its own, so per-message filters struggle to detect gradual escalation even when the attack pattern is known.

## 5. LLMs know their vulnerabilities: Uncover Safety Gaps through Natural Distribution Shifts

- **Authors:** Qibing Ren, Hao Li, Dongrui Liu, Zhanxu Xie, Xiaoya Lu, Yu Qiao, Lei Sha, Junchi Yan, Lizhuang Ma, Jing Shao
- **Venue:** Proceedings of the 63rd Annual Meeting of the ACL (Volume 1: Long Papers), pp. 24763–24785
- **Year:** 2025
- **DOI / ID:** 10.18653/v1/2025.acl-long.1207
- **Official URL:** https://aclanthology.org/2025.acl-long.1207/
- **Status:** verified (Update 1). Cite it only under its ACL Anthology title.
- **Why it matters:** The commercial analogue is reaching a policy bypass through related topics such as shipping, a competitor's policy or a "hypothetical" refund. This motivates the camouflaged pattern (Phase 3) and Phase 1's `hypothetical_framing` technique.
- **Scope (draft):** The paper studies how shifting a harmful request toward semantically related but innocuous-looking topics can expose safety gaps in aligned LLMs across multiple turns.
- **Methodology (draft):** The attack, ActorBreaker, draws on actor-network theory to identify "actors" (people, objects, concepts) linked to a harmful target and chains queries about them toward that target. The authors also build a multi-turn safety dataset for fine-tuning defenses.
- **Critical Takeaway (draft):** An attack can reach a harmful target through related concepts instead of explicit phrasing, so defenses keyed to that phrasing miss it.

## 6. Refusal in Language Models Is Mediated by a Single Direction

- **Authors:** Andy Arditi, Oscar Obeso, Aaquib Syed, Daniel Paleka, Nina Panickssery, Wes Gurnee, Neel Nanda
- **Venue:** Advances in Neural Information Processing Systems 37 (NeurIPS 2024), Main Conference Track
- **Year:** 2024
- **DOI / ID:** 10.52202/079017-4322
- **Official URL:** https://proceedings.neurips.cc/paper_files/paper/2024/hash/f545448535dfde4f9786555403ab7c49-Abstract-Conference.html
- **Status:** verified (Update 1)
- **Why it matters:**
  - It is the mechanistic basis for the Phase 2 hypothesis that a linear probe can read intent-relevant signal from hidden states.
  - The matched negatives are what make that test meaningful: the probe has to separate intent, not topic.
- **Scope (draft):** The paper shows that refusal in open-source chat models is mediated by a single direction in the residual stream: removing it disables refusal, and adding it induces refusal on harmless prompts.
- **Methodology (draft):** The direction is extracted as the difference in mean activations between harmful and harmless instructions, and is tested causally through directional ablation and activation addition. A rank-one weight edit based on it yields a white-box jailbreak.
- **Critical Takeaway (draft):** Safety behavior sits in a low-dimensional, fragile internal structure, which makes it easy to remove and also readable by probes.

## 7. τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains

- **Authors:** Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan
- **Venue:** International Conference on Learning Representations (ICLR 2025), pp. 9965–10017
- **Year:** 2025
- **DOI / ID:** none listed
- **Official URL:** https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html
- **Status:** verified 2026-10-18 on proceedings.iclr.cc
- **Why it matters:**
  - It is the standard setting for agents bound by domain policy guidelines in retail and airline customer service, and tau-break (paper 1) builds on it.
  - It supports EcomSafe's choice to ground every attack and negative in an explicit written store policy.
- **Scope (draft):** τ-bench evaluates language agents that talk with simulated users while following domain-specific policy guidelines and using API tools, in retail and airline customer-service domains.
- **Methodology (draft):** An LM simulates the user. Success is judged by comparing the final database state with an annotated goal state, and a pass^k metric measures how reliably an agent succeeds across repeated trials.
- **Critical Takeaway (draft):** Even strong function-calling agents follow domain rules inconsistently across repeated trials, so policy adherence must be measured directly instead of assumed.
- **Note:** any specific numbers quoted in the report must first be checked against the paper.

## 8. WildTeaming at Scale: From In-the-Wild Jailbreaks to (Adversarially) Safer Language Models

- **Authors:** Liwei Jiang, Kavel Rao, Seungju Han, et al. (11 authors; full list on the official page)
- **Venue:** Advances in Neural Information Processing Systems 37 (NeurIPS 2024), Main Conference Track, pp. 47094–47165
- **Year:** 2024
- **DOI / ID:** 10.52202/079017-1493
- **Official URL:** https://proceedings.neurips.cc/paper_files/paper/2024/hash/54024fca0cef9911be36319e622cde38-Abstract-Conference.html
- **Status:** verified 2026-10-18. This is the main track, not Datasets & Benchmarks.
- **Why it matters:** Its "contrastive" design pairs harmful queries with benign queries that resemble them in form. This is the closest peer-reviewed precedent for EcomSafe's matched negatives, and for the framing-preserving negatives in particular.
- **Scope (draft):** WildTeaming is an automatic red-teaming framework that mines in-the-wild user–chatbot interactions to discover jailbreak tactics and composes them into new adversarial attacks. The authors use it to build WildJailbreak, a large open safety-training dataset.
- **Methodology (draft):** WildJailbreak contains two contrastive kinds of queries: harmful queries, both plain and adversarial, and benign queries that resemble harmful ones in form but carry no harmful intent. The authors train models on it and evaluate both safety and over-refusal.
- **Critical Takeaway (draft):** A safety dataset needs benign counterparts that look adversarial in form, or a model can learn the surface form of an attack rather than its intent and over-refuse benign requests.

## 9. XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models

- **Authors:** Paul Röttger, Hannah Rose Kirk, Bertie Vidgen, Giuseppe Attanasio, Federico Bianchi, Dirk Hovy
- **Venue:** Proceedings of NAACL 2024 (Volume 1: Long Papers), pp. 5377–5400
- **Year:** 2024
- **DOI / ID:** 10.18653/v1/2024.naacl-long.301
- **Official URL:** https://aclanthology.org/2024.naacl-long.301/
- **Status:** verified 2026-10-18
- **Why it matters:**
  - It grounds EcomSafe's boundary cases: legitimate requests near a policy line, such as an honest price match or a question about an item just outside the return window, that a naive filter would wrongly block.
  - This matters because over-blocking legitimate shoppers has a direct business cost.
- **Scope (draft):** XSTest is a test suite for "exaggerated safety", where a model refuses clearly safe prompts because they superficially resemble unsafe ones.
- **Methodology (draft):** The suite pairs safe prompts from several prompt types (for example homonyms, figurative language and safe contexts) with contrasting unsafe prompts, and uses them to characterize refusal behavior across models.
- **Critical Takeaway (draft):** Models refuse safe requests that share vocabulary with unsafe ones, so safety evaluation needs explicit near-boundary benign cases.
- **Note:** prompt counts and per-model results to be quoted in the report must first be checked against the paper.

## 10. Annotation Artifacts in Natural Language Inference Data

- **Authors:** Suchin Gururangan, Swabha Swayamdipta, Omer Levy, Roy Schwartz, Samuel Bowman, Noah A. Smith
- **Venue:** Proceedings of NAACL-HLT 2018 (Volume 2: Short Papers), pp. 107–112
- **Year:** 2018
- **DOI / ID:** 10.18653/v1/N18-2017
- **Official URL:** https://aclanthology.org/N18-2017/
- **Status:** verified 2026-10-18
- **Why it matters:**
  - It is the methodological basis for EcomSafe's lexical shortcut audit, which asks whether a simple surface-word classifier can separate the classes.
  - It frames `pilot_150`'s 0.905 audit accuracy correctly: a sign of dataset artifacts, not a detection success.
- **Scope (draft):** The paper shows that crowd-sourced NLI datasets contain annotation artifacts: lexical and stylistic cues in the hypotheses that reveal the label without the premise.
- **Methodology (draft):** The authors train a text classifier on hypotheses alone, find that it predicts the label far above chance, analyze the cue words involved, and re-evaluate models on the "hard" subset that the hypothesis-only classifier gets wrong.
- **Critical Takeaway (draft):** When a classifier that sees only surface features succeeds, benchmark scores overstate understanding, so datasets should be audited and reported with such baselines.
- **Note:** the exact SNLI and MultiNLI percentages should be checked against the paper before quoting.

---

## Alternates (verified, not counted)

### Alt-A. JBShield: Defending Large Language Models from Jailbreak Attacks through Activated Concept Analysis and Manipulation

- **Authors:** Shenyi Zhang, Yuchen Zhai, Keyan Guo, et al. (10 authors)
- **Venue:** 34th USENIX Security Symposium (USENIX Security 25), pp. 8215–8234
- **Year:** 2025
- **DOI / ID:** none issued (USENIX)
- **Official URL:** https://www.usenix.org/conference/usenixsecurity25/presentation/zhang-shenyi
- **Status:** verified 2026-10-18
- **Why it matters:** It is a direct precedent for Phase 2: detecting jailbreaks from concepts in hidden representations. Its official page reports an average detection accuracy of 0.95 for JBShield-D (to be checked against the paper before quoting).
- **Scope (draft):** The paper defends LLMs against jailbreaks by analyzing which concepts are activated in their hidden representations.
- **Methodology (draft):** It identifies toxic and jailbreak concepts in the representation space. It uses them to detect jailbreak prompts (JBShield-D) and to suppress the jailbreak concept while strengthening the toxic one (JBShield-M).
- **Critical Takeaway (draft):** Jailbreak attempts leave detectable traces in internal representations, which supports representation-level detection as a baseline beyond text classifiers.

### Alt-B. Evaluating Models' Local Decision Boundaries via Contrast Sets

- **Authors:** Matt Gardner, Yoav Artzi, Victoria Basmov, et al. (26 authors)
- **Venue:** Findings of the Association for Computational Linguistics: EMNLP 2020, pp. 1307–1323
- **Year:** 2020
- **DOI / ID:** 10.18653/v1/2020.findings-emnlp.117
- **Official URL:** https://aclanthology.org/2020.findings-emnlp.117/
- **Status:** verified 2026-10-18 (Findings, which is peer-reviewed)
- **Why it matters:** Contrast sets are minimal edits that change the gold label. EcomSafe's matched negatives apply the same idea in reverse: the same product, policy topic and framing, with the intent changed.
- **Scope (draft):** The paper argues that standard test sets miss systematic gaps, and proposes contrast sets to evaluate a model's decision boundary around individual examples.
- **Methodology (draft):** Dataset authors manually perturb test instances in small but meaningful ways that change the gold label. They build contrast sets for many NLP datasets and compare model performance on original and perturbed examples.
- **Critical Takeaway (draft):** Models that score well on standard test sets often fail on minimally changed examples, so evaluation should include label-changing minimal pairs.

---

## Other verified peer-reviewed papers (pool, not selected)

These were verified on official pages on 2026-10-18 and may be cited as additional related work.

- **Zheng et al., Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena** (NeurIPS 2023, Datasets & Benchmarks; doi 10.52202/075280-2020). Relevant to the blind judge's biases.
- **Perez et al., Red Teaming Language Models with Language Models** (EMNLP 2022; doi 10.18653/v1/2022.emnlp-main.225). LM-generated test cases.
- **Andriushchenko et al., AgentHarm** (ICLR 2025). Each harmful behavior has a benign counterpart (stated in the official PDF).
- **Cui et al., OR-Bench** (ICML 2025, PMLR 267). Over-refusal at scale.
- **Han et al., WildGuard** (NeurIPS 2024, Datasets & Benchmarks; doi 10.52202/079017-0261). A candidate moderation-classifier baseline.
- **Xie et al., SORRY-Bench** (ICLR 2025). Judge meta-evaluation.
- **Liu et al., Formalizing and Benchmarking Prompt Injection Attacks and Defenses** (USENIX Security 2024). Relevant to the `instruction_injection` technique.
- **Zhou et al., How Alignment and Jailbreak Work: Explain LLM Safety through Intermediate Hidden States** (Findings of EMNLP 2024; doi 10.18653/v1/2024.findings-emnlp.139).

**Excluded:**
- Kaushik et al., counterfactually-augmented data (ICLR 2020): only partially verified, because OpenReview was blocked.

## Supporting / recent preprints (not counted)

None of these has a verified peer-reviewed venue. They may appear in a short "recent preprints" paragraph.

| Preprint | arXiv | Relevance |
|---|---|---|
| Shi et al., Organizational Control Layer: Governance Infrastructure at the Execution Boundary of LLM Agent Systems | 2606.04306 | A policy and economic-constraint layer that checks an agent's actions before they run |
| Zhai et al., SIA: A Synthesize-Inject-Align Framework for Knowledge-Grounded and Secure E-commerce Search LLMs with Industrial Deployment | 2603.16137 | Synthetic safety data and boundary cases for e-commerce LLMs. The PDF still carries an ACM template placeholder, so there is no venue. |
| Guida et al., Cognitive Firewall | 2607.01277 | Session-level gates |
| Sheoran and Hao, MultiTurnPSB | 2606.02630 | Multi-turn attacks and per-turn classifier defenses (medical domain) |
| Li et al., State-Dependent Safety Failures in Multi-Turn Language Model Interaction | 2603.15684 | How dialogue state drifts across turns |
| Zhou et al., Speak Out of Turn | 2402.17262 | Multi-turn decomposition |

**Unverified design-provenance names** appear in the `data_generation` code comments: CompliBench, the "Extreme Lowballer" buyer persona, and an LLM-to-LLM seller-jailbreak study. Do not cite these until a source is located and verified.
