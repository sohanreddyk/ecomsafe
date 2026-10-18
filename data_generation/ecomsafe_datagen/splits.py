"""
Leakage-safe splits.

The split unit is a connected component over (gen_group, pair_id):
  * all k variants from one generator call stay together (near-paraphrases),
  * an attack and its matched negative stay together (minimal pairs),
  * later, every turn of a multi-turn conversation is one record anyway.

Components are stratified by (domain, attack_type) so every split covers every
threat cell. `holdout_split` produces generalization splits for RQ4
(unseen domain / unseen technique / unseen attack type).
"""
from __future__ import annotations

import random
from collections import defaultdict

from .schema import Conversation


class _UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def components(convs: list[Conversation]) -> dict[str, list[Conversation]]:
    uf = _UF()
    for c in convs:
        uf.find("g:" + c.gen_group)
        if c.pair_id:
            uf.union("g:" + c.gen_group, "p:" + c.pair_id)
    comps = defaultdict(list)
    for c in convs:
        comps[uf.find("g:" + c.gen_group)].append(c)
    return comps


def _stratum(comp: list[Conversation]) -> tuple:
    a = next((c for c in comp if c.is_attack), comp[0])
    return (a.domain, a.attack_type or "none", a.negative_kind or "attack")


def grouped_split(convs: list[Conversation], ratios: dict[str, float], seed: int = 0) -> dict[str, list[Conversation]]:
    rng = random.Random(seed)
    by_stratum = defaultdict(list)
    for comp in components(convs).values():
        by_stratum[_stratum(comp)].append(comp)
    names = list(ratios)
    total = sum(len(c) for comps in by_stratum.values() for c in comps)
    target = {n: ratios[n] * total for n in names}
    filled = {n: 0 for n in names}
    out = {n: [] for n in names}
    keys = sorted(by_stratum)
    rng.shuffle(keys)                       # no stratum always goes first
    for key in keys:
        comps = by_stratum[key]
        rng.shuffle(comps)
        for comp in comps:
            # the split furthest below its global target share; random tie-break
            order = names[:]
            rng.shuffle(order)
            n = min(order, key=lambda n: filled[n] / (target[n] + 1e-9))
            out[n].extend(comp)
            filled[n] += len(comp)
    return out

def holdout_split(convs: list[Conversation], field: str, value: str,
                  val_ratio: float = 0.1, seed: int = 0) -> dict[str, list[Conversation]]:
    """field in {'domain','attack_type','technique'}; held-out value goes entirely to test.

    For a held-out attack type / technique, the matched negatives of those attacks
    go to test too (they share components), so test keeps both classes.
    """
    def has_value(comp):
        for c in comp:
            if field == "technique":
                if any(t.label and t.label.technique == value for t in c.user_turns if c.is_attack):
                    return True
            elif getattr(c, field) == value:
                return True
        return False

    test, rest = [], []
    for comp in components(convs).values():
        (test if has_value(comp) else rest).extend(comp)
    inner = grouped_split(rest, {"train": 1 - val_ratio, "val": val_ratio}, seed)
    return {"train": inner["train"], "val": inner["val"], "test": test}
