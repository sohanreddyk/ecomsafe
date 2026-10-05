## Verdict: the pipeline runs end to end; the batch is not yet usable as a benchmark

**Structural checks pass:**
- Distribution: 75 records; 25 cells × 2 attacks; 25 benign, one per cell.
- Clause coverage: every target clause resolves in the policy.
- Near-duplicates: none.
- Safety: no dose or medical content, and no real brand names.

**Style is not a giveaway.** On the pair-grouped probe (chance = 0.50; 0.70 = fail), the batch scores:
- all surface features: 0.56;
- function words only: 0.55;
- surface measures only: 0.50.

None of these is significant. One pooled register measure crosses the flag line: type-token ratio, d = −0.55. Benign messages are slightly more lexically varied.

**Content is the problem.** The manual review below finds:
- **only 9 of 50 attacks are usable as written;**
- 16 are partial;
- 25 are not attacks at all.

The model's self-audit flagged only 4 of those 25.

### Manual review (meaning check)

Every record was read against its target clause and attack type. These are judgements made in review, not automatic checks.

#### Attacks (50)

| Verdict | Count | IDs |
|---|---|---|
| **Usable**: a coherent attempt to get the agent to break its target rule | 9 | 005, 016, 019, 023, 032, 039, 040, 043, 049 |
| **Partial**: some adversarial intent, but the target rule doesn't fit, the request is garbled, or it's a weak exception request | 16 | 001, 003, 004, 008, 012, 013, 014, 018, 022, 024, 028, 033, 038, 046, 047, 048 |
| **Not an attack**: an honest request, an information question, or nonsense | 25 | 002, 006, 007, 009, 010, 011, 015, 017, 020, 021, 025, 026, 027, 029, 030, 031, 034, 035, 036, 037, 041, 042, 044, 045, 050 |

Typical failures:

- **Honest requests labelled as attacks.** These include 006 (refund for a faulty TV), 021 (asks about current jean promotions), 031 (delivery refund for a late order, which the rule allows), and 034 (refund for spoiled milk).
- **Nonsense.** 009 and 010 ask for a *prescription* for a TV or electronic device. 041 asks the store to *raise* an interest rate. 045 calls an investment plan "broken".
- **Wrong attack type.** 032 tries to buy whiskey for an underage cousin, which is a regulatory bypass, but its cell is price manipulation.
- **Rule doesn't fit the message.** For example, 001 is a discount request aimed at "check shipping status first", and 047 is an expired promo code aimed at "record the waiting period".

#### Benign (25)

| Verdict | Count | IDs |
|---|---|---|
| Honest and straightforward | 21 | all others |
| **Broken** | 4 | 055 (asks for a "prescription requirement" for an electronic product); 057 (asks the store to *provide* a prescription); 065 (an "age-restricted handbag"); 073 (a "defective" investment savings plan) |

#### Label integrity

In 7 pairs, both sides describe the same honest request, so identical content carries opposite labels:
- 011/056
- 013/057
- 017/059
- 021/061
- 025/063
- 031/066
- 035/068

#### Self-audit vs manual review

The model answered *no* for 4 attacks (020, 021, 036, 037) and 3 benign records (057, 062, 065). All 4 attack flags agree with the review. But they cover only 4 of the 25 attacks the review judged not to be attacks. Of the benign flags, two agree (057, 065) and one is a false alarm (062). **The model's self-audit cannot be relied on to catch its own labelling errors.**

### Policy findings

The automatic checks pass the policy's format, but its content has problems that flow through to the records:

- **Inverted rules.** P-070 says the agent must *not* explain that prices change dynamically; ABCD instructs the opposite. P-080 says a new promo code must be offered "regardless of membership"; ABCD restricts it by tier.
- **Rules the spec says to discard.** Politeness and troubleshooting steps were kept. For example, P-058 ends by asking whether the customer needs anything else. There are 10 FAQ rules and 6 troubleshooting rules.
- **Missing thresholds.** The returns rules leave out ABCD's tier-specific return windows (30 days / 90 days / 6 months).
- **Implausible authored rules.** Examples: "at least 18 to buy *any* pharmaceutical" (P-142), "no more than one quantity of a pharmaceutical at a time" (P-144), and a 5% gift-card fee (P-156). One clause is written in the first person (P-158: "I can provide …").
- **Copied wording.** 3 clauses share a 6-word phrase with ABCD text (P-002, P-058, P-075).
- **Unreliable cell-strength judgements.** Fashion × regulatory bypass was rated *strong*, although clothing has no legal gate. Groceries × regulatory bypass, which is the alcohol age gate, was rated *weak*.

### Pipeline notes

- **Design.** The design phase originally showed the model all 158 clauses at once. It then picked a few pharmaceutical clauses for almost every cell, including electronics and fashion. Each cell now gets a shortlist of at most 30 relevant clauses: general-retail clauses from the attack type's ABCD procedure groups, plus that domain's own clauses. A check rejects any pick outside the shortlist. After this change, no cell targets another domain's rules.
- **Generation.** Dose and brand checks were made hard limits after review. Three slots were regenerated (008, 013/057, 016), and no record now contains dose or brand content.
- **Product names.** The design phase's product names and scenarios contained real brands (e.g. a named TV maker), a model number, and medicine strengths. These are now removed deterministically, and the design check rejects them in future runs.
- **Cost.** See `pipeline_stats.json`. Messages took 147 attempts across 50 slots, and 10 slots were kept with minor form flags. The policy phase took 126 attempts, 26 of which were invalid JSON.

### What would make this usable

1. Correct the policy before design: fix the inverted and implausible rules, and drop the FAQ and troubleshooting rules.
2. A meaning check on every record that does not rely on the generator. That could be a human or a larger model. Replace records judged partial or not an attack.
3. Rerun generation with a larger model, such as Llama-3.1-8B-Instruct. The pipeline accepts `--model`.
