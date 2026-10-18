"""
Human validation.

export_blind_sample: stratified sample -> annotation CSV without labels, plus a
separate key file. Over-samples judge disagreements/soft agreements so human
effort goes where labels are least certain.

score_annotations: compares a completed CSV against the key and reports
Cohen's kappa (human vs. design label, human vs. judge) and a confusion matrix.
Report these numbers in the paper's dataset section.
"""
from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict

from .schema import Conversation

LABELS = ["PV", "CD", "FF", "RB", "BENIGN"]


def export_blind_sample(convs: list[Conversation], n: int, out_csv: str, key_csv: str,
                        uncertain_share: float = 0.3, seed: int = 0) -> int:
    rng = random.Random(seed)
    uncertain = [c for c in convs if c.qc.get("judge", {}).get("verdict") not in (None, "agree")]
    unc_ids = {c.conv_id for c in uncertain}
    certain = [c for c in convs if c.conv_id not in unc_ids]
    n_unc = min(len(uncertain), int(n * uncertain_share))
    strata = defaultdict(list)
    for c in certain:
        strata[(c.domain, c.attack_type, c.negative_kind)].append(c)
    picked = rng.sample(uncertain, n_unc)
    per = max(1, (n - n_unc) // max(1, len(strata)))
    for v in strata.values():
        picked += rng.sample(v, min(per, len(v)))
    rng.shuffle(picked)
    with open(out_csv, "w", newline="", encoding="utf-8") as f, open(key_csv, "w", newline="", encoding="utf-8") as k:
        w, kw = csv.writer(f), csv.writer(k)
        w.writerow(["item_id", "domain", "context", "message", "label(PV/CD/FF/RB/BENIGN)", "realistic(y/n)", "notes"])
        kw.writerow(["item_id", "conv_id", "gold", "judge"])
        for i, c in enumerate(picked):
            users = c.user_turns
            ctx = " || ".join(f"{t.role}: {t.content}" for t in c.turns[:-1]) if len(users) > 1 else ""
            w.writerow([i, c.domain, ctx, c.primary_text, "", "", ""])
            gold = max(users, key=lambda t: t.label.risk_target).label.intent
            j = c.qc.get("judge", {}).get("turns", [{}])
            kw.writerow([i, c.conv_id, gold, j[-1].get("intent", "") if j else ""])
    return len(picked)


def cohen_kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] * cb[l] for l in set(a) | set(b)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def score_annotations(annot_csv: str, key_csv: str) -> dict:
    key = {r["item_id"]: r for r in csv.DictReader(open(key_csv, encoding="utf-8"))}
    human, gold, judge = [], [], []
    col = "label(PV/CD/FF/RB/BENIGN)"
    for r in csv.DictReader(open(annot_csv, encoding="utf-8")):
        lab = (r.get(col) or "").strip().upper()
        if lab in LABELS and r["item_id"] in key:
            human.append(lab)
            gold.append(key[r["item_id"]]["gold"])
            judge.append(key[r["item_id"]]["judge"])
    conf = {g: Counter(h for h, gg in zip(human, gold) if gg == g) for g in LABELS}
    return {"n": len(human),
            "kappa_human_vs_design": round(cohen_kappa(human, gold), 4),
            "kappa_human_vs_judge": round(cohen_kappa(human, judge), 4),
            "confusion_gold_to_human": {g: dict(c) for g, c in conf.items()}}
