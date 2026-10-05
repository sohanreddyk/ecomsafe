"""Validate an EcomSafeBench pilot batch-1 directory and write <dir>/batch1_validation.md.

Checks (numbering follows the Phase 4 task spec):
1. Distribution: 2 attacks per cell, 10 per attack type, 10 per domain; 25 benign
   records, one per cell, 5 per domain and 5 per attack type.
2. Clause coverage: every target_clause_id resolves in the policy file.
3. Near-duplicates: all-MiniLM-L6-v2 embeddings, pairwise cosine in plain numpy.
   Pairs > 0.85 are flagged, excluding intended minimal pairs, whose
   similarities are reported separately.
4. Register parity: attack vs benign on token length, punctuation density,
   typo (out-of-vocabulary) rate, type-token ratio, and a few extra surface
   measures. Uses Cohen's d and a Mann-Whitney U p-value; |d| >= 0.5 is flagged.
5. Style-leak probe: logistic regression on surface features only (no content
   words, no embeddings), 5-fold stratified CV repeated 20 times.
   Classes are imbalanced (50 vs 25), so a constant "attack" guess scores 0.67
   accuracy. Balanced accuracy and ROC AUC are therefore the headline numbers
   (chance = 0.50), with a permutation test. Further runs use only the benign
   prompts and their paired attacks (true minimal pairs), including
   pair-grouped CV, which keeps both members of a pair in the same fold.
6. Lexical diversity: distinct-2 per group, plus distinct-2 for attacks
   resampled to the benign count (distinct-n falls with corpus size).
7. Self-audit: appended from <dir>/batch1_self_audit.md (written separately).

Typo counting: a token is out-of-vocabulary if neither it nor a simple
inflectional stem is in /usr/share/dict/words, a contraction list, or the
domain allowlist below. OOV tokens are listed in the report so false
positives can be checked by eye.

Usage:
  .venv/bin/python scripts/validate_batch1.py                         # Llama/data with Llama/policy
  .venv/bin/python scripts/validate_batch1.py --dir DIR --policy POLICY.md
"""

import argparse

import json
import re
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, RepeatedStratifiedKFold, StratifiedKFold, cross_validate, permutation_test_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RECORDS = Path("Llama/data/batch1_records.jsonl")
POLICY = Path("Llama/policy/ecomsafe_policy_llama.md")
SELF_AUDIT = Path("Llama/data/batch1_self_audit.md")
OUT_MD = Path("Llama/data/batch1_validation.md")
OUT_JSON = Path("Llama/data/batch1_validation_metrics.json")
DUP_THRESHOLD = 0.85
N_BENIGN = 25          # one benign companion per cell
PAIR_LEN_TOL = 0.25    # within-pair token-length tolerance
SEED = 0

# Standard English function words: articles, pronouns, prepositions,
# conjunctions, auxiliaries, determiners, common adverbial particles.
FUNCTION_WORDS = sorted(set("""
a an the this that these those my your his her its our their me you him us them i we he she it they
mine yours myself yourself
of in on at by for with about from to into onto over under after before between through during without
within against off out up down than as
and or but so if because though although while when where whether then also not no nor
is am are was were be been being do does did doing have has had having will would shall should can could
may might must
what which who whom whose how why
all any some each every both either neither other another such more most much many few
just only very too really even still already again
there here now
""".split()))

CONTRACTIONS = set("""
i'm i've i'd i'll you're you've you'd you'll he's she's it's we're we've they're they've
don't doesn't didn't can't couldn't won't wouldn't isn't aren't wasn't weren't haven't hasn't
shouldn't that's there's what's let's who's she'd she'll he'd he'll we'd we'll they'd they'll
""".split())

# Domain terms and product vocabulary absent from the system word list.
ALLOWLIST = set("""
mah ebt bnpl apr esrb er otc rx copay medicare tricare medicaid pseudoephedrine amoxicillin
selvedge cashmere sequin deli rotisserie nevada canada tuesday saturday sunday friday elm
4k 55 11 13 16 17 8 10 30 35 40 48 150 180 300 999 1 240 1,240 20,000 12
okay email app subbed
box laptop tv mom fax promo intro mirrorless decongestant electronically heard paid held
""".split())

PUNCT = set(".,?!'\"-:;()/$&%")


def load():
    return [json.loads(l) for l in RECORDS.read_text().splitlines() if l.strip()]


def tokens(s):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9',]*[A-Za-z0-9]|[A-Za-z0-9]", s)


def words_lower(s):
    return [t.lower().strip("'") for t in re.findall(r"[A-Za-z][A-Za-z']*", s)]


def load_dict():
    return {w.strip().lower() for w in Path("/usr/share/dict/words").read_text().splitlines()}


def stems(w):
    out = [w]
    if w.endswith("ies"):
        out.append(w[:-3] + "y")
    if w.endswith("es"):
        out.append(w[:-2])
    if w.endswith("s"):
        out.append(w[:-1])
    if w.endswith("ied"):
        out.append(w[:-3] + "y")
    if w.endswith("ed"):
        out += [w[:-2], w[:-1], w[:-3] if len(w) > 4 and w[-3] == w[-4] else w[:-2]]
    if w.endswith("ing"):
        out += [w[:-3], w[:-3] + "e", w[:-4] if len(w) > 5 and w[-4] == w[-5] else w[:-3]]
    if w.endswith("ly"):
        out.append(w[:-2])
    if w.endswith("er"):
        out += [w[:-2], w[:-1]]
    if w.endswith("'s"):
        out.append(w[:-2])
    return out


def oov_tokens(s, vocab):
    bad = []
    for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9',]*", s):
        w = t.lower().rstrip(",'")
        if not w or w in CONTRACTIONS or w in ALLOWLIST or re.fullmatch(r"[\d,.$]+", w):
            continue
        if any(x in vocab or x in ALLOWLIST for x in stems(w)):
            continue
        if "-" in w and all(p in vocab for p in w.split("-")):
            continue
        bad.append(w)
    return bad


def surface(s, vocab):
    toks = tokens(s)
    n = max(len(toks), 1)
    wl = words_lower(s)
    punct = [c for c in s if c in PUNCT]
    letters = [c for c in s if c.isalpha()]
    oov = oov_tokens(s, vocab)
    return {
        "n_tokens": len(toks),
        "n_chars": len(s),
        "mean_word_len": float(np.mean([len(w) for w in wl])) if wl else 0.0,
        "punct_density": len(punct) / n,
        "typo_count": len(oov),
        "typo_rate": len(oov) / n,
        "ttr": len(set(wl)) / max(len(wl), 1),
        "lowercase_initial": float(s[:1].islower()),
        "uppercase_ratio": sum(c.isupper() for c in letters) / max(len(letters), 1),
        "n_sentences": max(len(re.findall(r"[.?!]+(\s|$)", s)), 1),
        "n_question": s.count("?"),
        "n_period": s.count("."),
        "n_comma": s.count(","),
        "n_apostrophe": s.count("'"),
        "n_exclaim": s.count("!"),
        "n_digit": sum(c.isdigit() for c in s),
        "ends_with_punct": float(s.rstrip()[-1:] in ".?!"),
    }


def cohens_d(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((a.mean() - b.mean()) / sp) if sp > 0 else 0.0


def distinct2(prompts):
    bg = []
    for p in prompts:
        w = words_lower(p)
        bg += list(zip(w, w[1:]))
    return len(set(bg)) / max(len(bg), 1)


def feature_matrix(prompts, vocab):
    rows, names = [], None
    for p in prompts:
        f = surface(p, vocab)
        wl = words_lower(p)
        n = max(len(wl), 1)
        c = Counter(wl)
        for fw in FUNCTION_WORDS:
            f[f"fw_{fw}"] = c[fw] / n
        names = names or list(f)
        rows.append([f[k] for k in names])
    return np.array(rows), names


def probe(X, y, label):
    pipe = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight="balanced", max_iter=5000))
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=SEED)
    res = cross_validate(pipe, X, y, cv=cv, scoring=["accuracy", "balanced_accuracy", "roc_auc"])
    score, perm_scores, p = permutation_test_score(
        pipe, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
        scoring="balanced_accuracy", n_permutations=1000, random_state=SEED)
    pipe.fit(X, y)
    return {
        "label": label, "n": int(len(y)), "n_pos": int(y.sum()),
        "majority_baseline_acc": float(max(y.mean(), 1 - y.mean())),
        "accuracy_mean": float(res["test_accuracy"].mean()), "accuracy_sd": float(res["test_accuracy"].std()),
        "balanced_acc_mean": float(res["test_balanced_accuracy"].mean()),
        "balanced_acc_sd": float(res["test_balanced_accuracy"].std()),
        "auc_mean": float(res["test_roc_auc"].mean()), "auc_sd": float(res["test_roc_auc"].std()),
        "perm_balanced_acc": float(score), "perm_null_mean": float(perm_scores.mean()),
        "perm_null_95th": float(np.percentile(perm_scores, 95)), "perm_p": float(p),
        "coef": pipe[-1].coef_[0],
    }


def grouped_probe(X, y, groups, label, repeats=20):
    """Pair-grouped CV: both members of a minimal pair always land in the same fold.

    Ungrouped CV on matched pairs can score *below* chance: the held-out
    prompt's near-identical twin is in training with the opposite label.
    Grouping removes that artefact, so this is the fair minimal-pair test.
    """
    pipe = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight="balanced", max_iter=5000))
    rng = np.random.default_rng(SEED)
    ba, auc = [], []
    uniq = np.unique(groups)
    for _ in range(repeats):
        relabel = dict(zip(uniq, rng.permutation(len(uniq))))
        g = np.array([relabel[x] for x in groups])
        res = cross_validate(pipe, X, y, groups=g, cv=GroupKFold(5), scoring=["balanced_accuracy", "roc_auc"])
        ba += list(res["test_balanced_accuracy"])
        auc += list(res["test_roc_auc"])
    score, perm_scores, p = permutation_test_score(
        pipe, X, y, groups=groups, cv=GroupKFold(5), scoring="balanced_accuracy",
        n_permutations=1000, random_state=SEED)
    return {"label": label, "n": int(len(y)), "balanced_acc_mean": float(np.mean(ba)),
            "balanced_acc_sd": float(np.std(ba)), "auc_mean": float(np.mean(auc)), "auc_sd": float(np.std(auc)),
            "perm_null_95th": float(np.percentile(perm_scores, 95)), "perm_p": float(p)}


def main():
    global RECORDS, SELF_AUDIT, OUT_MD, OUT_JSON, POLICY
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="Llama/data", help="directory holding batch1_records.jsonl; outputs go here too")
    ap.add_argument("--policy", default=str(POLICY), help="policy file the records' clause IDs refer to")
    cli = ap.parse_args()
    d, POLICY = Path(cli.dir), Path(cli.policy)
    RECORDS, SELF_AUDIT = d / "batch1_records.jsonl", d / "batch1_self_audit.md"
    OUT_MD, OUT_JSON = d / "batch1_validation.md", d / "batch1_validation_metrics.json"
    recs = load()
    attacks = [r for r in recs if r["record_type"] == "attack"]
    benign = [r for r in recs if r["record_type"] == "benign"]
    by_id = {r["id"]: r for r in recs}
    md, metrics = [], {}
    P = md.append

    P("# EcomSafeBench Pilot Batch 1: Validation Report\n")
    P(f"Generated by `scripts/validate_batch1.py` from `{RECORDS}`. "
      f"The verdict and Section 7 are written separately (`{OUT_MD.parent / 'batch1_verdict.md'}`, `{SELF_AUDIT}`).\n")
    verdict = OUT_MD.parent / "batch1_verdict.md"
    if verdict.exists():
        P(verdict.read_text().strip() + "\n")

    # 1. distribution
    cells = Counter((r["product_domain"], r["attack_type"]) for r in attacks)
    by_type = Counter(r["attack_type"] for r in attacks)
    by_dom = Counter(r["product_domain"] for r in attacks)
    b_cells = Counter((by_id[r["paired_with"]]["product_domain"], by_id[r["paired_with"]]["attack_type"]) for r in benign)
    b_dom = Counter(r["product_domain"] for r in benign)
    b_type = Counter(by_id[r["paired_with"]]["attack_type"] for r in benign)
    checks = {
        f"{50 + N_BENIGN} records": len(recs) == 50 + N_BENIGN,
        f"50 attacks / {N_BENIGN} benign": (len(attacks), len(benign)) == (50, N_BENIGN),
        "25 cells x 2 attacks": len(cells) == 25 and set(cells.values()) == {2},
        "10 attacks per attack type": set(by_type.values()) == {10} and len(by_type) == 5,
        "10 attacks per domain": set(by_dom.values()) == {10} and len(by_dom) == 5,
        f"{N_BENIGN} benign in {N_BENIGN} distinct cells": len(b_cells) == N_BENIGN and set(b_cells.values()) == {1},
        f"{N_BENIGN // 5} benign per domain": set(b_dom.values()) == {N_BENIGN // 5} and len(b_dom) == 5,
        f"{N_BENIGN // 5} benign per attack type": set(b_type.values()) == {N_BENIGN // 5} and len(b_type) == 5,
        "benign directly follows its paired attack": all(
            recs[i - 1]["id"] == r["paired_with"] for i, r in enumerate(recs) if r["record_type"] == "benign"),
        "benign shares domain and clause with pair": all(
            by_id[r["paired_with"]]["product_domain"] == r["product_domain"]
            and by_id[r["paired_with"]]["target_clause_id"] == r["target_clause_id"] for r in benign),
        "unique IDs": len({r["id"] for r in recs}) == len(recs),
    }
    metrics["distribution"] = checks
    P("## 1. Distribution\n")
    P("| Check | Result |\n|---|---|")
    for k, v in checks.items():
        P(f"| {k} | {'PASS' if v else '**FAIL**'} |")
    P("\nWeak cells (tagged, kept by decision): "
      + ", ".join(sorted({f"{r['product_domain']} x {r['attack_type']}" for r in attacks if r["cell_strength"] == "weak"}))
      + ".\n")

    # 2. clause coverage
    clause_ids = set(re.findall(r"^### (P-\d{3}) \|", POLICY.read_text(), re.M))
    unresolved = [r["id"] for r in recs if r["target_clause_id"] not in clause_ids]
    used = Counter(r["target_clause_id"] for r in recs)
    metrics["clause_coverage"] = {"unresolved": unresolved, "distinct_clauses_used": len(used)}
    P("## 2. Clause coverage\n")
    P(f"- Unresolved `target_clause_id`: **{len(unresolved)}** {unresolved if unresolved else ''}")
    P(f"- Distinct clauses targeted: {len(used)} of {len(clause_ids)} in the policy.")
    P(f"- Most-targeted: {', '.join(f'{k} ({v})' for k, v in used.most_common(5))}.\n")

    # 3. near duplicates
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    emb = model.encode([r["prompt"] for r in recs], normalize_embeddings=True)
    S = emb @ emb.T
    pairs_intended = {frozenset((r["id"], r["paired_with"])) for r in benign}
    flagged, pair_sims = [], []
    for i, j in combinations(range(len(recs)), 2):
        key = frozenset((recs[i]["id"], recs[j]["id"]))
        if key in pairs_intended:
            pair_sims.append((recs[j]["paired_with"] if recs[j]["record_type"] == "benign" else recs[i]["paired_with"],
                              recs[j]["id"] if recs[j]["record_type"] == "benign" else recs[i]["id"], float(S[i, j])))
        elif S[i, j] > DUP_THRESHOLD:
            flagged.append((recs[i]["id"], recs[j]["id"], float(S[i, j])))
    off = S[np.triu_indices(len(recs), 1)]
    non_pair_max = max(float(S[i, j]) for i, j in combinations(range(len(recs)), 2)
                       if frozenset((recs[i]["id"], recs[j]["id"])) not in pairs_intended)
    top_nonpair = sorted(
        ((recs[i]["id"], recs[j]["id"], float(S[i, j])) for i, j in combinations(range(len(recs)), 2)
         if frozenset((recs[i]["id"], recs[j]["id"])) not in pairs_intended), key=lambda x: -x[2])[:5]
    metrics["near_duplicates"] = {"threshold": DUP_THRESHOLD, "flagged": flagged,
                                  "minimal_pair_sims": pair_sims, "max_non_pair": non_pair_max}
    P("## 3. Near-duplicate check\n")
    P(f"Model `all-MiniLM-L6-v2`, cosine similarity on normalised embeddings, threshold {DUP_THRESHOLD}.\n")
    P(f"- Flagged non-pair duplicates: **{len(flagged)}**")
    for a, b, s in flagged:
        P(f"  - {a} / {b}: {s:.3f}")
    P(f"- Highest non-pair similarity: {non_pair_max:.3f}. Mean pairwise similarity: {off.mean():.3f}.")
    P("- Top 5 non-pair similarities: " + "; ".join(f"{a}/{b} {s:.3f}" for a, b, s in top_nonpair) + ".\n")
    P("Intended minimal pairs (excluded from flagging):\n")
    P("| Attack | Benign | Cosine |\n|---|---|---|")
    for a, b, s in sorted(pair_sims):
        P(f"| {a} | {b} | {s:.3f} |")
    ps = [s for *_, s in pair_sims]
    P(f"\nMinimal-pair cosine: mean {np.mean(ps):.3f}, min {min(ps):.3f}, max {max(ps):.3f}.\n")

    # 4. register parity
    vocab = load_dict()
    fa = [surface(r["prompt"], vocab) for r in attacks]
    fb = [surface(r["prompt"], vocab) for r in benign]
    fpaired = [surface(by_id[r["paired_with"]]["prompt"], vocab) for r in benign]
    measures = ["n_tokens", "n_chars", "punct_density", "typo_count", "typo_rate", "ttr",
                "mean_word_len", "lowercase_initial", "uppercase_ratio", "n_sentences",
                "n_question", "n_exclaim", "ends_with_punct"]
    primary = {"n_tokens", "punct_density", "typo_count", "ttr"}
    parity, loud = {}, []
    P("## 4. Register parity (attack vs benign)\n")
    P("Effect size is Cohen's d (attack minus benign). |d| ≥ 0.5 is flagged, and |d| ≥ 0.8 is flagged loudly. "
      "The p-value is a two-sided Mann-Whitney U test. The *paired attacks* column covers only the attacks that have a benign companion. "
      "Rows marked ★ are the four measures the task spec requires. "
      "*d (paired)* compares the paired attacks with their benign companions, the comparison that matters for minimal pairs.\n")
    P(f"| Measure | Attack (n=50) mean ± sd | Benign (n={len(benign)}) mean ± sd | Paired attacks (n={len(benign)}) mean | d (all) | p (all) | d (paired) | Flag |")
    P("|---|---|---|---|---|---|---|---|")
    for m in measures:
        a = [x[m] for x in fa]
        b = [x[m] for x in fb]
        pa = [x[m] for x in fpaired]
        d = cohens_d(a, b)
        try:
            p = float(mannwhitneyu(a, b).pvalue)
        except ValueError:
            p = 1.0
        dp = cohens_d(pa, b)
        worst = max(abs(d), abs(dp))
        flag = "**LARGE**" if worst >= 0.8 else ("flag" if worst >= 0.5 else "")
        if flag:
            loud.append((m, d, p, dp))
        parity[m] = {"attack_mean": float(np.mean(a)), "attack_sd": float(np.std(a, ddof=1)),
                     "benign_mean": float(np.mean(b)), "benign_sd": float(np.std(b, ddof=1)),
                     "paired_attack_mean": float(np.mean(pa)), "d": d, "p": p, "d_paired": dp}
        star = " ★" if m in primary else ""
        P(f"| {m}{star} | {np.mean(a):.3f} ± {np.std(a, ddof=1):.3f} | {np.mean(b):.3f} ± {np.std(b, ddof=1):.3f} "
          f"| {np.mean(pa):.3f} | {d:+.2f} | {p:.3f} | {dp:+.2f} | {flag} |")
    metrics["register_parity"] = parity
    P("")
    if loud:
        P("**Measures over the |d| ≥ 0.5 flag line (either comparison):** " + "; ".join(
            f"`{m}` d(all)={d:+.2f} (p={p:.3f}), d(paired)={dp:+.2f}" for m, d, p, dp in loud) + ".\n")
    else:
        P("**No measure reaches |d| ≥ 0.5.**\n")
    P("### 4b. Within-pair register match\n")
    P(f"Each benign record should match its paired attack's register: token length within ±{PAIR_LEN_TOL:.0%}, "
      "the same initial casing, and the same end punctuation. Speech act is recorded so that crossing can be checked: "
      "Q = the prompt contains a question mark, D = it doesn't.\n")
    P("| Attack | Benign | Tokens (A/B) | Ratio | Casing match | End-punct match | Speech act (A/B) |")
    P("|---|---|---|---|---|---|---|")
    mism, acts = [], Counter()
    for b in benign:
        a = by_id[b["paired_with"]]
        ta, tb = len(tokens(a["prompt"])), len(tokens(b["prompt"]))
        ratio = tb / ta
        cas = a["prompt"][:1].islower() == b["prompt"][:1].islower()
        endp = (a["prompt"].rstrip()[-1:] in ".?!") == (b["prompt"].rstrip()[-1:] in ".?!")
        sa = "Q" if "?" in a["prompt"] else "D"
        sb = "Q" if "?" in b["prompt"] else "D"
        acts[(sa, sb)] += 1
        ok_len = abs(ratio - 1) <= PAIR_LEN_TOL
        if not (ok_len and cas and endp):
            mism.append(b["id"])
        P(f"| {a['id']} | {b['id']} | {ta}/{tb} | {ratio:.2f}{'' if ok_len else ' **✗**'} | "
          f"{'yes' if cas else '**no**'} | {'yes' if endp else '**no**'} | {sa}/{sb} |")
    P(f"\nPairs failing a register-match criterion: **{len(mism)}** {mism if mism else ''}")
    P("Speech-act combinations (attack/benign): " + ", ".join(f"{k[0]}/{k[1]}: {v}" for k, v in sorted(acts.items())))
    qa = sum("?" in r["prompt"] for r in attacks) / len(attacks)
    qb = sum("?" in r["prompt"] for r in benign) / len(benign)
    P(f"Question-form share: attacks {qa:.0%} (all 50), benign {qb:.0%}.\n")
    metrics["pair_register"] = {"mismatched": mism, "speech_acts": {f"{k[0]}/{k[1]}": v for k, v in acts.items()},
                                "question_share_attack": qa, "question_share_benign": qb}

    oov_a = Counter(w for r in attacks for w in oov_tokens(r["prompt"], vocab))
    oov_b = Counter(w for r in benign for w in oov_tokens(r["prompt"], vocab))
    P("Out-of-vocabulary tokens counted as typos, listed for manual checking:")
    P(f"- attack: {dict(oov_a.most_common())}")
    P(f"- benign: {dict(oov_b.most_common())}\n")

    # 5. style-leak probe
    X, names = feature_matrix([r["prompt"] for r in recs], vocab)
    y = np.array([1 if r["record_type"] == "benign" else 0 for r in recs])
    full = probe(X, y, f"all {len(recs)} (50 attack / {len(benign)} benign)")
    idx = [i for i, r in enumerate(recs) if r["record_type"] == "benign"
           or r["id"] in {b["paired_with"] for b in benign}]
    nb = len(benign)
    bal = probe(X[idx], y[idx], f"{nb} benign vs their {nb} paired attacks")
    n_surf = len(names) - len(FUNCTION_WORDS)
    abl = [probe(X[idx][:, :n_surf], y[idx], f"paired {nb}v{nb}, surface measures only"),
           probe(X[idx][:, n_surf:], y[idx], f"paired {nb}v{nb}, function words only")]
    pair_of = {}
    for k, r in enumerate(benign):
        pair_of[r["id"]] = k
        pair_of[r["paired_with"]] = k
    groups = np.array([pair_of[recs[i]["id"]] for i in idx])
    grp = [grouped_probe(X[idx], y[idx], groups, f"paired {nb}v{nb}, all surface features"),
           grouped_probe(X[idx][:, :n_surf], y[idx], groups, f"paired {nb}v{nb}, surface measures only"),
           grouped_probe(X[idx][:, n_surf:], y[idx], groups, f"paired {nb}v{nb}, function words only")]
    P("## 5. Style-leak probe\n")
    P(f"Logistic regression (standardised features, L2, C=1, class-balanced weights) on **{X.shape[1]} surface features**: "
      f"{len(names) - len(FUNCTION_WORDS)} length/punctuation/case/typo/TTR measures and {len(FUNCTION_WORDS)} function-word relative "
      "frequencies. No content words, no embeddings. Scores are 5-fold stratified CV repeated 20 times; the permutation test "
      "uses 1,000 label shuffles on balanced accuracy.\n")
    P("| Run | n | Majority-class accuracy | Accuracy | **Balanced accuracy** | ROC AUC | Permutation null 95th pct | p |")
    P("|---|---|---|---|---|---|---|---|")
    for rr in (full, bal, *abl):
        P(f"| {rr['label']} | {rr['n']} | {rr['majority_baseline_acc']:.2f} | {rr['accuracy_mean']:.2f} ± {rr['accuracy_sd']:.2f} "
          f"| **{rr['balanced_acc_mean']:.2f} ± {rr['balanced_acc_sd']:.2f}** | {rr['auc_mean']:.2f} ± {rr['auc_sd']:.2f} "
          f"| {rr['perm_null_95th']:.2f} | {rr['perm_p']:.3f} |")
    P("")
    P(f"Raw accuracy on the full set is not comparable to the task's ~0.50 expectation. A constant \"attack\" guess already scores {full['majority_baseline_acc']:.2f}. "
      "Balanced accuracy and AUC have a chance level of 0.50 in every run, and the paired runs are the direct minimal-pair test.\n")
    P("**Pair-grouped CV** (both members of each pair in the same fold; 5 folds, 20 group shuffles; permutation test 1,000). "
      "This is the fair minimal-pair test: ungrouped CV on matched pairs is biased *below* chance, because each test prompt's twin "
      "is in training with the opposite label.\n")
    P("| Run | n | **Balanced accuracy** | ROC AUC | Permutation null 95th pct | p |")
    P("|---|---|---|---|---|---|")
    for g in grp:
        P(f"| {g['label']} | {g['n']} | **{g['balanced_acc_mean']:.2f} ± {g['balanced_acc_sd']:.2f}** | "
          f"{g['auc_mean']:.2f} ± {g['auc_sd']:.2f} | {g['perm_null_95th']:.2f} | {g['perm_p']:.3f} |")
    P("")
    metrics["style_leak_grouped"] = grp
    order = np.argsort(-np.abs(full["coef"]))[:10]
    P("Top 10 features by |coefficient| (full-set model; positive means it predicts benign):\n")
    P("| Feature | Coef |\n|---|---|")
    for k in order:
        P(f"| {names[k]} | {full['coef'][k]:+.2f} |")
    P("")
    metrics["style_leak"] = {k: {kk: vv for kk, vv in v.items() if kk != "coef"} for k, v in (("full", full), ("balanced", bal), ("paired_surface_only", abl[0]), ("paired_function_words_only", abl[1]))}

    # 6. distinct-2
    rng = np.random.default_rng(SEED)
    pa_all = [r["prompt"] for r in attacks]
    sub = [distinct2(list(rng.choice(pa_all, len(benign), replace=False))) for _ in range(500)]
    d2 = {"attack_all_50": distinct2(pa_all), "benign": distinct2([r["prompt"] for r in benign]),
          "attack_resampled_mean": float(np.mean(sub)), "attack_resampled_sd": float(np.std(sub)),
          "paired_attacks": distinct2([by_id[r["paired_with"]]["prompt"] for r in benign])}
    metrics["distinct2"] = d2
    P("## 6. Lexical diversity (distinct-2)\n")
    P("| Set | distinct-2 |\n|---|---|")
    P(f"| Attacks, all 50 | {d2['attack_all_50']:.3f} |")
    P(f"| Attacks, random {nb} (500 resamples) | {d2['attack_resampled_mean']:.3f} ± {d2['attack_resampled_sd']:.3f} |")
    P(f"| The {nb} paired attacks | {d2['paired_attacks']:.3f} |")
    P(f"| Benign, {nb} | {d2['benign']:.3f} |")
    P("\ndistinct-n falls as a corpus grows, so the size-matched rows are the fair comparison.\n")

    # 7. self-audit
    P("## 7. Self-audit\n")
    P(SELF_AUDIT.read_text().strip() if SELF_AUDIT.exists() else "_Not yet written._")
    P("")

    OUT_MD.write_text("\n".join(md) + "\n")
    OUT_JSON.write_text(json.dumps(metrics, indent=2, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
    print("\n".join(md))


if __name__ == "__main__":
    main()
