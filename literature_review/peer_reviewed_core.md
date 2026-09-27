# Peer-Reviewed Core Set: Background & Related Work

**Course requirement:** at least 5 peer-reviewed conference or journal papers.
**Status: 5 papers count. 1 candidate is uncertain and is not counted.**

Verification date: 2026-09-27. Only official proceedings or publisher pages are accepted as proof of venue. arXiv-only work is not counted.

See the **Final verification table** at the end of this file for the one-row-per-paper status.

**Verification levels:**
- **[OP]** The official page was opened and its metadata was read directly.
- **[OS]** An official-domain URL was found in search results, but the page itself could not be opened in this session. Venue and title come from the search listing of that page.
- **[Verified]** Full bibliographic metadata (authors, venue, DOI) confirmed by the author on 2026-09-27, on top of the official URLs found earlier.

---

## 1. Crescendo [OP]

- **Exact title:** Great, Now Write an Article About That: The Crescendo Multi-Turn LLM Jailbreak Attack
- **Authors:** Mark Russinovich (Microsoft Azure), Ahmed Salem (Microsoft), Ronen Eldan (Microsoft)
- **Year:** 2025
- **Venue:** 34th USENIX Security Symposium (USENIX Security 25), pp. 2421–2440. ISBN 978-1-939133-52-6.
- **Official URL:** https://www.usenix.org/conference/usenixsecurity25/presentation/russinovich
- **PDF:** https://www.usenix.org/system/files/conference/usenixsecurity25/sec25cycle1-prepub-805-russinovich.pdf
- **DOI:** None listed on the USENIX page. USENIX does not issue DOIs.
- **Counts toward requirement:** **Yes.** USENIX Security is a peer-reviewed top-tier security conference.

**Scope:** Introduces Crescendo, a multi-turn jailbreak that opens with benign, abstract questions about a task. Over successive turns it escalates the conversation until the model produces content it would refuse if asked directly.
**Methodology:** The authors run Crescendo manually against commercial and open models, including ChatGPT, Gemini Pro, and LLaMA variants. They also automate it as *Crescendomation* and evaluate it on an AdvBench subset, where it beats prior jailbreaks by 29–61% on GPT-4 and 49–71% on Gemini-Pro.
**Critical Takeaway:** Each individual turn looks benign, so per-message filters struggle to detect gradual escalation even when the attack pattern is known.
**Relevance to EcomSafe:** Crescendo is the canonical form of the gradual, "linear" escalation pattern in EcomSafe's taxonomy. Its benign-per-turn property directly motivates EcomSafe's trajectory features, such as escalation delta and running mean, over per-message classification.

---

## 2. LLMs know their vulnerabilities: Uncover Safety Gaps through Natural Distribution Shifts (Ren et al., ACL 2025) [OP]

- **Exact title (as published):** LLMs know their vulnerabilities: Uncover Safety Gaps through Natural Distribution Shifts
- **Authors:** Qibing Ren, Hao Li, Dongrui Liu, Zhanxu Xie, Xiaoya Lu, Yu Qiao, Lei Sha, Junchi Yan, Lizhuang Ma, Jing Shao
- **Year:** 2025
- **Venue:** Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), pp. 24763–24785. The ACL Anthology page lists an **Outstanding Paper** award.
- **Official URL:** https://aclanthology.org/2025.acl-long.1207/
- **DOI:** 10.18653/v1/2025.acl-long.1207
- **Counts toward requirement:** **Yes.**

> **Citation rule:** Cite only the ACL Anthology title, DOI, and pages above. Do not use the informal preprint title (arXiv 2410.10700) anywhere in the paper. The ACL paper counts on its own merits as a peer-reviewed ACL 2025 Long paper.

**Scope:** Studies how an attacker can shift the distribution of a harmful request toward semantically related but innocuous-looking topics, and exploit that shift over multiple turns to jailbreak aligned LLMs.
**Methodology:** ActorBreaker draws on Latour's actor-network theory. It identifies "actors" (people, objects, concepts) linked to a harmful target and uses them to build multi-turn query chains that gradually reach the target. The authors also build a multi-turn safety dataset for fine-tuning defenses.
**Critical Takeaway:** Models can generate the associations that lead to their own jailbreak, so blocking the explicit harmful phrasing misses attacks that approach the target through related concepts.
**Relevance to EcomSafe:** In commerce, the same indirect route shows up as policy bypass reached through tangential topics (shipping, a competitor's policy, "hypothetical" refunds). This matches the "camouflaged" escalation pattern EcomSafe defines, and supports probing latent intent rather than surface keywords.

---

## 3. Speak Out of Turn: NOT COUNTED (uncertain)

- **Exact title:** Speak Out of Turn: Safety Vulnerability of Large Language Models in Multi-turn Dialogue
- **Authors:** Zhenhong Zhou et al. The full list was not checked against an official page.
- **Year:** 2024 (arXiv)
- **Venue:** **None found.** A search restricted to ACL Anthology returned only the arXiv version (https://arxiv.org/abs/2402.17262). I found no official proceedings or publisher page.
- **DOI:** None found.
- **Counts toward requirement:** **No.** Venue status is uncertain, so under the course rules it is not counted.

**Scope:** Argues that single-turn safety alignment does not transfer to multi-turn dialogue. It shows that a malicious query can be split into sub-queries whose combined answers are harmful.
**Methodology:** Proposes a prompting paradigm, executable by humans or LLMs, that decomposes a harmful request into multi-turn sub-queries. The paradigm is evaluated on widely used commercial LLMs, followed by an analysis of causes and mitigation strategies.
**Critical Takeaway:** Harm can be spread across turns so that no single response is objectionable, but the assembled dialogue is.
**Relevance to EcomSafe:** Decomposition is a plausible route to competitor-data extraction or regulatory bypass. The paper can be cited as background, but it must not count toward the 5-paper requirement unless a peer-reviewed version is confirmed on an official page.

---

## 4. HarmBench [OP]

- **Exact title:** HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal
- **Authors:** Mantas Mazeika, Long Phan, Xuwang Yin, Andy Zou, Zifan Wang, Norman Mu, Elham Sakhaee, Nathaniel Li, Steven Basart, Bo Li, David Forsyth, Dan Hendrycks
- **Year:** 2024
- **Venue:** Proceedings of the 41st International Conference on Machine Learning (ICML 2024), PMLR vol. 235, pp. 35181–35224
- **Official URL:** https://proceedings.mlr.press/v235/mazeika24a.html
- **DOI:** None. PMLR does not issue DOIs.
- **Counts toward requirement:** **Yes.**

**Scope:** Provides a standardized evaluation framework for automated red-teaming attacks and for measuring how robustly LLMs refuse harmful requests.
**Methodology:** The authors define desirable properties for red-teaming evaluation and build a behavior set and scoring pipeline to meet them. They then compare 18 red-teaming methods against 33 target LLMs and defenses, and propose an efficient adversarial-training defense.
**Critical Takeaway:** Attack success rates are not comparable across papers without a shared threat model, behavior set, and judge, so evaluation protocol is itself a research contribution.
**Relevance to EcomSafe:** HarmBench is the reference design for reproducible scoring. EcomSafe's commercial attack classes and judge should report results in a similarly standardized way, so that its numbers can be compared with baselines.

---

## 5. JailbreakBench [Verified]

- **Exact title:** JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models
- **Authors:** Patrick Chao, Edoardo Debenedetti, Alexander Robey, Maksym Andriushchenko, Francesco Croce, Vikash Sehwag, Edgar Dobriban, Nicolas Flammarion, George J. Pappas, Florian Tramèr, Hamed Hassani, Eric Wong
- **Year:** 2024
- **Venue:** Advances in Neural Information Processing Systems 37 (NeurIPS 2024), Datasets and Benchmarks Track
- **Official URL:** https://proceedings.neurips.cc/paper_files/paper/2024/hash/63092d79154adebd7305dfd498cbff70-Abstract-Datasets_and_Benchmarks_Track.html
- **DOI:** 10.52202/079017-1745
- **Counts toward requirement:** **Yes.** The NeurIPS Datasets & Benchmarks Track is peer-reviewed and published in the NeurIPS proceedings.
- **Verification status:** Fully verified (title, authors, venue, year, DOI).

**Scope:** Addresses inconsistent and irreproducible jailbreak evaluation with an open, standardized benchmark.
**Methodology:** The benchmark releases an evolving repository of jailbreak prompts ("artifacts"), a dataset of 100 misuse behaviors, a standardized evaluation framework with a defined threat model and scoring, and a public leaderboard.
**Critical Takeaway:** Many jailbreak results cannot be reproduced because prompts, code, or model versions were withheld, so releasing artifacts is necessary for credible comparison.
**Relevance to EcomSafe:** EcomSafe should release its commercial attack dialogues and judge prompts as artifacts in the JailbreakBench style, and report false positives on benign shopping dialogues alongside attack success.

---

## 6. Refusal Direction [Verified]

- **Exact title:** Refusal in Language Models Is Mediated by a Single Direction
- **Authors:** Andy Arditi, Oscar Obeso, Aaquib Syed, Daniel Paleka, Nina Panickssery, Wes Gurnee, Neel Nanda
- **Year:** 2024
- **Venue:** Advances in Neural Information Processing Systems 37 (NeurIPS 2024), Main Conference Track
- **Official URL:** https://proceedings.neurips.cc/paper_files/paper/2024/hash/f545448535dfde4f9786555403ab7c49-Abstract-Conference.html
- **PDF:** https://proceedings.neurips.cc/paper_files/paper/2024/file/f545448535dfde4f9786555403ab7c49-Paper-Conference.pdf
- **DOI:** 10.52202/079017-4322
- **Counts toward requirement:** **Yes.** The venue is confirmed by the official proceedings URL.
- **Verification status:** Fully verified (title, authors, venue, year, DOI).

**Scope:** Shows that refusal in open-source chat models is mediated by a single direction in the residual stream: removing it disables refusal, and adding it induces refusal on harmless prompts.
**Methodology:** The authors extract the direction as the difference in mean activations between harmful and harmless instructions. They test it causally by directional ablation and activation addition. They also show that a rank-one weight edit produces a white-box jailbreak that is simpler than fine-tuning.
**Critical Takeaway:** Safety fine-tuning is concentrated in a low-dimensional, fragile structure, which makes it easy to remove but also easy to read.
**Relevance to EcomSafe:** This is the mechanistic basis for EcomSafe's hidden-state intent probe. It also underlies the refusal-direction projections used by Li et al. [SDSF], which the existing related work already discusses. The same fragility is a threat-model caveat: a white-box adversary can suppress exactly this signal.

---

## Final verification table

| # | Exact title | Authors | Venue | Year | Official URL | DOI | Counts toward requirement |
|---|---|---|---|---|---|---|---|
| 1 | Great, Now Write an Article About That: The Crescendo Multi-Turn LLM Jailbreak Attack | Mark Russinovich, Ahmed Salem, Ronen Eldan | 34th USENIX Security Symposium (USENIX Security 25), pp. 2421–2440 | 2025 | https://www.usenix.org/conference/usenixsecurity25/presentation/russinovich | None issued (USENIX) | **Yes** |
| 2 | LLMs know their vulnerabilities: Uncover Safety Gaps through Natural Distribution Shifts | Qibing Ren, Hao Li, Dongrui Liu, Zhanxu Xie, Xiaoya Lu, Yu Qiao, Lei Sha, Junchi Yan, Lizhuang Ma, Jing Shao | Proceedings of the 63rd Annual Meeting of the ACL (Volume 1: Long Papers), pp. 24763–24785 | 2025 | https://aclanthology.org/2025.acl-long.1207/ | 10.18653/v1/2025.acl-long.1207 | **Yes** |
| 3 | HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal | Mantas Mazeika, Long Phan, Xuwang Yin, Andy Zou, Zifan Wang, Norman Mu, Elham Sakhaee, Nathaniel Li, Steven Basart, Bo Li, David Forsyth, Dan Hendrycks | Proceedings of the 41st International Conference on Machine Learning (ICML 2024), PMLR 235, pp. 35181–35224 | 2024 | https://proceedings.mlr.press/v235/mazeika24a.html | None issued (PMLR) | **Yes** |
| 4 | JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models | Patrick Chao, Edoardo Debenedetti, Alexander Robey, Maksym Andriushchenko, Francesco Croce, Vikash Sehwag, Edgar Dobriban, Nicolas Flammarion, George J. Pappas, Florian Tramèr, Hamed Hassani, Eric Wong | NeurIPS 2024 (Advances in Neural Information Processing Systems 37), Datasets and Benchmarks Track | 2024 | https://proceedings.neurips.cc/paper_files/paper/2024/hash/63092d79154adebd7305dfd498cbff70-Abstract-Datasets_and_Benchmarks_Track.html | 10.52202/079017-1745 | **Yes** |
| 5 | Refusal in Language Models Is Mediated by a Single Direction | Andy Arditi, Oscar Obeso, Aaquib Syed, Daniel Paleka, Nina Panickssery, Wes Gurnee, Neel Nanda | NeurIPS 2024 (Advances in Neural Information Processing Systems 37), Main Conference Track | 2024 | https://proceedings.neurips.cc/paper_files/paper/2024/hash/f545448535dfde4f9786555403ab7c49-Abstract-Conference.html | 10.52202/079017-4322 | **Yes** |
| 6 | Speak Out of Turn: Safety Vulnerability of Large Language Models in Multi-turn Dialogue | Zhenhong Zhou et al. | No peer-reviewed venue independently verified (arXiv 2402.17262 only) | 2024 | https://arxiv.org/abs/2402.17262 (preprint, not an official venue page) | None found | **No** |

**Rows marked Yes: 5.** The course requirement (≥ 5 peer-reviewed conference or journal papers) is met.

All five counted papers have verified title, authors, venue, year, and official source. JailbreakBench and Refusal Direction metadata, including DOIs, were confirmed on 2026-09-27.

**Remaining checks before submission:**
- Speak Out of Turn stays uncounted unless a peer-reviewed version is independently verified on an official proceedings or publisher page. It may still be cited as background (arXiv preprint).

`paper/related_work.md` was not modified.
