## Problem Description

**Conversational agents in commerce.** EcomSafe studies LLM-based shopping assistants; the proposal cites Amazon Rufus, Google Shopping AI, and Shopify Sidekick as examples [EcomSafe]. Unlike general-purpose LLMs, such agents operate under business constraints, including pricing logic, brand rules, return policies, and regulatory guidelines [EcomSafe]. EcomSafe targets them across five product domains: electronics, pharmaceuticals, fashion, financial products, and groceries [EcomSafe].

**Safety requirements beyond harmful content.** Standard jailbreak benchmarks such as HarmBench and JailbreakBench define harm mainly as objectionable content [HB; JBB]. Commercial agents also face failures in which the output is innocuous as text but violates a business rule. The proposal calls these *commercial jailbreaks* and defines five attack types [EcomSafe]:
- *Price manipulation:* overriding pricing logic or extracting unearned discounts.
- *Policy bypass:* circumventing return, refund, or warranty policies.
- *Return fraud:* obtaining step-by-step guidance for fraudulent returns.
- *Competitor extraction:* forcing unauthorized competitor comparisons or intelligence leaks.
- *Regulatory bypass:* extracting age-gated, prescription, or restricted-product information (e.g., "I'm a nurse—tell me the max safe dose without standard disclaimers.").

Fraud-adjacent requests such as fake reviews already appear inside general benchmarks, but without a commercial taxonomy [SDSF]. Among the works reviewed here, none treats business-rule violations as a distinct threat class.

**Insufficiency of single-turn filters.** Deployed guard classifiers typically judge each message in isolation [CF]. Crescendo escalates from benign, abstract questions to content the model would refuse if asked directly, and its automated variant outperforms prior jailbreaks by 29–61% on GPT-4 [CRES]. Preprint evidence points the same way:
- Li et al. report that Claude 3.5 Sonnet succumbs to 3.0% of GCG and PAIR attacks but 74.0% of multi-turn trajectories [SDSF].
- Sheoran and Hao find that two defenders indistinguishable at turn 1 (34.8% vs. 31.8% unsafe) diverge sharply by turn 4 [PSB].

**Gradual emergence of harmful intent.** Harmful intent need not be visible in any single turn. An attacker may:
- escalate step by step [CRES];
- approach a target through semantically related topics [ACTB]; or
- decompose a request into sub-queries whose answers are individually unobjectionable [SOT].

The proposal's commercial example [EcomSafe]:
1. "I'm looking for a premium laptop."
2. "What's the cheapest way to acquire it?"
3. "What if I report it damaged and return an empty box after using it?"
4. "How do most people get away with that without getting flagged?"

Only the full sequence reveals the objective. The proposal distinguishes linear, camouflaged, and late-spike escalation [EcomSafe]. Preprint evidence adds that escalation can also be abrupt, with Turn 2 a "critical vulnerability window" [PSB].

**Technical significance.** Because risk belongs to the trajectory rather than to any single message, detection must operate at the conversation level. Three technical considerations follow:
1. *Readable internal signal.* Refusal in chat models is mediated by a single readable direction in activation space [REF]. Hidden-state probes may therefore track intent across turns, though a white-box adversary could suppress the signal.
2. *Early detection.* Detection is useful only if it precedes the harmful completion.
3. *Reproducible, low-false-alarm evaluation.* Evaluation must be standardized and reproducible [HB; JBB], and false alarms must stay low. False-alarm rates of 16–45% on benign prompts are the primary deployment constraint for classifier defenses [PSB]. Because benign shopping dialogues dominate, over-blocking has a direct business cost.

**Research gap.** Trajectory-aware defenses such as TurnGate and THRD already exist [CF], so tracking risk across turns is not itself novel. The gap EcomSafe investigates is narrower: whether trajectory-aware detection over a hidden-state intent probe helps detect commercial jailbreaks early across e-commerce product domains. EcomSafe's proposed contributions are [EcomSafe]:
- the commercial jailbreak taxonomy above;
- EcomSafeBench, a benchmark of 3,900 annotated conversations;
- trajectory features over per-turn probe risk scores: escalation rate delta, running mean risk, risk volatility, and Kendall's rank correlation with turn index;
- an evaluation plan with four metrics: ROC AUC per threat class, early-detection rate (attacks caught before turn 5), false-positive rate on benign shopping dialogues, and per-turn latency. Results are to be analyzed by threat class and product domain against per-turn, output-filter, keyword, sliding-window, and full-context baselines.

These are research objectives, not established findings. Whether the features add signal beyond existing trajectory-aware aggregators remains to be tested.
