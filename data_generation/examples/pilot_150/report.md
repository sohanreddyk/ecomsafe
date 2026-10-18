# EcomSafeBench data report: pilot_150

Generator: `openai/gpt-oss-120b` | Judge: `qwen/qwen3.8-27b` | prompts `st-v2.4`


## Funnel

| stage | n |
|---|---|
| generated | 392 |
| after rule filter | 392 |
| after near-dup filter | 392 |
| after blind judge (+repair) | 375 |
| after pair integrity | 361 |
| after stratified trim | 289 |

## Composition

By class: {'attack': 126, 'benign/matched': 126, 'benign/boundary': 37}

Splits: {'train': 195, 'val': 35, 'test': 59}

## Attacks: domain x type

| domain | competitor_extraction | policy_bypass | price_manipulation | regulatory_bypass | return_fraud |
|---|---|---|---|---|---|
| electronics | 9 | 9 | 5 | 4 | 9 |
| fashion | 5 | 0 | 0 | 0 | 4 |
| financial_products | 0 | 10 | 5 | 8 | 0 |
| groceries | 6 | 8 | 10 | 8 | 0 |
| pharmaceuticals | 8 | 0 | 0 | 15 | 3 |

## Shortcut audit (attack vs matched negative, bag-of-ngrams NB, grouped CV)

Accuracy: **0.9048** (HIGH lexical separability: inspect top n-grams and regenerate negatives to mirror them)

By technique: {'authority_claim': 0.9091, 'coercion_threat': 0.9714, 'direct': 0.875, 'emotional_appeal': 0.9091, 'hypothetical_framing': 0.92, 'instruction_injection': 0.8696, 'persona_override': 1.0, 'policy_misquote': 0.8824}

Top attack n-grams: make, exception, an_exception, competitor, margin, and_give, though, even_though, bypass, online, you_make, override, bypass_the, cost, ignore_the

Top negative n-grams: price_match, your_catalog, me_what, what_verification, in_your, know_how, current, is_required, catalog, i_will, what_the, options, within_the, according, according_to

## Rejections

{'judge:disagree': 17, 'pairing:pair_orphan': 14}

Generation errors: {'attacks:generator_refusal': 6}

Matched-negative repair: {'attempted': 91, 'fixed': 63}

## Generator refusals (all attempts, including ones rescued by a retry)

By attack type: {'competitor_extraction': '0/10 (0%)', 'policy_bypass': '0/7 (0%)', 'price_manipulation': '0/4 (0%)', 'regulatory_bypass': '0/11 (0%)', 'return_fraud': '22/26 (85%)'}

By technique: {'authority_claim': '3/6 (50%)', 'coercion_threat': '1/6 (17%)', 'direct': '0/3 (0%)', 'emotional_appeal': '3/5 (60%)', 'hypothetical_framing': '1/8 (12%)', 'instruction_injection': '11/16 (69%)', 'persona_override': '0/3 (0%)', 'policy_misquote': '3/11 (27%)'}
