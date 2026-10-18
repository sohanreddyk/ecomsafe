"""
Quality control.

1. RuleFilter     - length, generator refusals, meta-word leakage, label words.
2. NearDupFilter  - MinHash-LSH on character shingles (stdlib only), applied per
                    class so an attack is never removed for resembling its own
                    matched negative (minimal pairs are the point).
3. BlindJudge     - an independent model relabels each user turn without seeing
                    the intended label. Disagreements are dropped (or kept and
                    flagged for human review). PV<->FF is treated as a soft,
                    configurable confusion because the boundary is genuinely fuzzy.
4. shortcut_audit - trains a bag-of-ngrams Naive Bayes on attack vs matched
                    negative with GROUPED cross-validation. If surface words alone
                    separate the classes, a hidden-state probe could be learning
                    lexicon or framing rather than intent. Reports the top
                    discriminative n-grams and per-technique accuracy so you know
                    what to regenerate.
"""
from __future__ import annotations

import math
import random
import re
import zlib
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Optional

from .domains import DOMAINS
from .llm import LLMClient, LLMRequest, QuotaExhaustedError, parse_json
from .prompts import BANNED_META_WORDS, JUDGE_LABELS, judge_prompt, judge_system
from .schema import Conversation

_REFUSAL_ANY = re.compile(r"(as an ai|i can(?:no|[’'])t help|i[’']?m sorry, but|language model)", re.I)
_LABEL_TOKENS = re.compile(r"\b(PV|CD|FF|RB|BENIGN|policy violation|fraud facilitation)\b")


def normalize(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s$%]", " ", t.lower())).strip()


# --------------------------------------------------------------------------- #
class RuleFilter:
    def __init__(self, min_chars: int = 15, max_chars: int = 700):
        self.min_chars, self.max_chars = min_chars, max_chars

    def reasons(self, c: Conversation) -> list[str]:
        r = []
        for t in c.user_turns:
            s = t.content
            if len(s) < self.min_chars:
                r.append("too_short")
            if len(s) > self.max_chars:
                r.append("too_long")
            if _REFUSAL_ANY.search(s):
                r.append("refusal_text")
            low = s.lower()
            if any(w in low for w in BANNED_META_WORDS):
                r.append("meta_word")
            if _LABEL_TOKENS.search(s):
                r.append("label_leak")
        return sorted(set(r))


# --------------------------------------------------------------------------- #
class NearDupFilter:
    """MinHash LSH; Jaccard threshold on character 5-gram shingles."""

    _P = (1 << 61) - 1

    def __init__(self, threshold: float = 0.8, num_perm: int = 64, bands: int = 16, seed: int = 0):
        assert num_perm % bands == 0
        self.threshold, self.num_perm, self.bands = threshold, num_perm, bands
        self.rows = num_perm // bands
        rng = random.Random(seed)
        self._ab = [(rng.randrange(1, self._P), rng.randrange(0, self._P)) for _ in range(num_perm)]

    @staticmethod
    def shingles(text: str, n: int = 5) -> set[int]:
        t = normalize(text)
        if len(t) <= n:
            return {zlib.crc32(t.encode())}
        return {zlib.crc32(t[i:i + n].encode()) for i in range(len(t) - n + 1)}

    def signature(self, sh: set[int]) -> list[int]:
        return [min(((a * h + b) % self._P) for h in sh) for a, b in self._ab]

    def filter(self, items: list[Conversation]) -> tuple[list[Conversation], list[tuple[Conversation, str]]]:
        """Keep the first occurrence; returns (kept, [(dropped, kept_conv_id)])."""
        buckets: dict[tuple, list[int]] = defaultdict(list)
        kept, kept_sh, dropped = [], [], []
        for c in items:
            text = " ".join(t.content for t in c.user_turns)
            sh = self.shingles(text)
            sig = self.signature(sh)
            keys = [(b, tuple(sig[b * self.rows:(b + 1) * self.rows])) for b in range(self.bands)]
            dup_of = None
            for cand in {i for k in keys for i in buckets.get(k, [])}:
                inter = len(sh & kept_sh[cand])
                if inter / (len(sh | kept_sh[cand]) or 1) >= self.threshold:
                    dup_of = kept[cand].conv_id
                    break
            if dup_of:
                dropped.append((c, dup_of))
                continue
            idx = len(kept)
            kept.append(c)
            kept_sh.append(sh)
            for k in keys:
                buckets[k].append(idx)
        return kept, dropped


# --------------------------------------------------------------------------- #
_INTENT_ALIASES = {
    "PV": "PV", "POLICY VIOLATION": "PV", "POLICY_VIOLATION": "PV",
    "CD": "CD", "COMPETITIVE DISCLOSURE": "CD", "COMPETITIVE_DISCLOSURE": "CD",
    "FF": "FF", "FRAUD FACILITATION": "FF", "FRAUD_FACILITATION": "FF",
    "RB": "RB", "REGULATORY BREACH": "RB", "REGULATORY_BREACH": "RB",
    "BENIGN": "BENIGN", "NONE": "BENIGN", "SAFE": "BENIGN", "LEGITIMATE": "BENIGN",
}
_INTENT_RE = re.compile(r"\b(PV|CD|FF|RB|BENIGN|policy violation|competitive disclosure|"
                        r"fraud facilitation|regulatory breach)\b", re.I)


def normalize_intent(value) -> str:
    """Map 'PV', 'pv', 'Policy Violation', 'PV (policy violation)', or a free-text answer
    to a canonical label. Small models rarely answer with the bare code."""
    if not isinstance(value, str) or not value.strip():
        return "UNPARSEABLE"
    v = value.strip().upper()
    if v in _INTENT_ALIASES:
        return _INTENT_ALIASES[v]
    found = {_INTENT_ALIASES[m.upper()] for m in _INTENT_RE.findall(value)}
    return found.pop() if len(found) == 1 else "UNPARSEABLE"


def _as_bool(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() not in ("false", "no", "0", "n")
    return bool(v)


# --------------------------------------------------------------------------- #
class BlindJudge:
    def __init__(self, client: LLMClient, soft_confusions: Iterable[tuple[str, str]] = (("PV", "FF"),),
                 min_confidence: float = 0.5, require_realistic: bool = True, max_workers: int = 8,
                 retries: int = 1):
        self.client, self.retries = client, retries
        self.soft = {frozenset(p) for p in soft_confusions}
        self.min_conf, self.require_realistic, self.max_workers = min_confidence, require_realistic, max_workers

    def _judge_turn(self, c: Conversation, turn_idx: int) -> dict:
        users = c.user_turns
        t = users[turn_idx]
        history = []
        for prev in c.turns:
            if prev is t:
                break
            history.append((prev.role, prev.content))
        pol = DOMAINS[c.domain].policy_for(c.policy_topic) if c.domain in DOMAINS else None
        data, intent, empty = {}, "UNPARSEABLE", False
        for attempt in range(self.retries + 1):
            req = LLMRequest(judge_system(), judge_prompt(c.domain, t.content, history, pol), "judge",
                             meta={"expected_intent": t.label.intent if t.label else "BENIGN"},  # MockClient only
                             temperature=0.0 if attempt == 0 else 0.3, max_tokens=200, seed=attempt)
            raw = self.client.complete(req)
            empty = not raw.strip()          # silent refusal: the model returned nothing at all
            data = parse_json(raw) or {}
            intent = normalize_intent(data.get("intent")) if data else normalize_intent(raw)
            if intent != "UNPARSEABLE":
                break
        conf = data.get("confidence", 0.7 if intent != "UNPARSEABLE" else 0)
        try:
            conf = float(conf)
        except (TypeError, ValueError):
            conf = 0.0
        return {"intent": intent, "severity": data.get("severity"), "empty": empty and intent == "UNPARSEABLE",
                "realistic": _as_bool(data.get("realistic", True)),
                "confidence": conf, "rationale": str(data.get("rationale", ""))[:200]}

    def _safe_judge_turn(self, c: Conversation, turn_idx: int) -> dict:
        """One failed judge call (provider outage, timeout) becomes a 'judge_error' verdict instead of
        crashing the run; it is not cached, so a rerun tries it again. Quota exhaustion still stops."""
        try:
            return self._judge_turn(c, turn_idx)
        except QuotaExhaustedError:
            raise
        except Exception as e:  # noqa: BLE001
            return {"intent": "UNPARSEABLE", "error": f"{type(e).__name__}: {str(e)[:120]}", "severity": None,
                    "realistic": True, "confidence": 0.0, "rationale": "", "empty": False}

    def _verdict(self, gold: str, j: dict) -> str:
        if j.get("error"):
            return "judge_error"
        if j["intent"] == "UNPARSEABLE":
            return "judge_refusal" if j.get("empty") else "judge_unparseable"
        if self.require_realistic and not j["realistic"]:
            return "unrealistic"
        if j["intent"] == gold:
            return "agree" if j["confidence"] >= self.min_conf else "low_confidence"
        if frozenset((gold, j["intent"])) in self.soft:
            return "soft_agree"
        return "disagree"

    def judge(self, convs: list[Conversation], turns: str = "attack_turns") -> None:
        """Annotates c.qc['judge'] in place.

        turns="attack_turns": judge only the decisive user turn(s) (all of them for
        single-turn). turns="all": judge every user turn (use for multi-turn audits).
        """
        jobs = []
        for c in convs:
            for i, t in enumerate(c.user_turns):
                if turns == "all" or len(c.user_turns) == 1 or (t.label and t.label.severity >= 2):
                    jobs.append((c, i))
        with ThreadPoolExecutor(self.max_workers) as ex:
            results = list(ex.map(lambda ci: self._safe_judge_turn(*ci), jobs))
        per_conv: dict[str, list] = defaultdict(list)
        for (c, i), j in zip(jobs, results):
            gold = c.user_turns[i].label.intent
            per_conv[c.conv_id].append({"turn": i + 1, "gold": gold, **j, "verdict": self._verdict(gold, j)})
        for c in convs:
            v = per_conv.get(c.conv_id, [])
            verdicts = {x["verdict"] for x in v}
            overall = "agree"
            for bad in ("judge_error", "disagree", "judge_refusal", "judge_unparseable", "unrealistic", "low_confidence",
                        "soft_agree"):
                if bad in verdicts:
                    overall = bad
                    break
            c.qc["judge"] = {"model": self.client.model, "turns": v, "verdict": overall}


# --------------------------------------------------------------------------- #
# Shortcut / leakage audit
# --------------------------------------------------------------------------- #
def _ngrams(text: str) -> list[str]:
    toks = normalize(text).split()
    return toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]


class _NB:
    def fit(self, X: list[list[str]], y: list[int]):
        self.cnt = [Counter(), Counter()]
        self.prior = [0, 0]
        for x, lab in zip(X, y):
            self.cnt[lab].update(x)
            self.prior[lab] += 1
        self.vocab = set(self.cnt[0]) | set(self.cnt[1])
        self.tot = [sum(c.values()) for c in self.cnt]
        return self

    def logp(self, w: str, lab: int) -> float:
        return math.log((self.cnt[lab][w] + 1) / (self.tot[lab] + len(self.vocab)))

    def predict(self, x: list[str]) -> int:
        s = [math.log(self.prior[k] + 1) + sum(self.logp(w, k) for w in x if w in self.vocab) for k in (0, 1)]
        return int(s[1] > s[0])


def shortcut_audit(convs: list[Conversation], folds: int = 5, seed: int = 0, top_k: int = 20) -> dict:
    """Attack (1) vs matched negative (0), grouped by pair component."""
    data = [c for c in convs if c.is_attack or c.negative_kind == "matched"]
    groups = sorted({c.gen_group for c in data})
    random.Random(seed).shuffle(groups)
    fold_of = {g: i % folds for i, g in enumerate(groups)}
    correct, by_tech = 0, defaultdict(lambda: [0, 0])
    for f in range(folds):
        tr = [c for c in data if fold_of[c.gen_group] != f]
        te = [c for c in data if fold_of[c.gen_group] == f]
        if not tr or not te:
            continue
        nb = _NB().fit([_ngrams(c.primary_text) for c in tr], [int(c.is_attack) for c in tr])
        for c in te:
            ok = nb.predict(_ngrams(c.primary_text)) == int(c.is_attack)
            correct += ok
            tech = c.user_turns[-1].label.technique if c.user_turns[-1].label else "?"
            by_tech[tech][0] += ok
            by_tech[tech][1] += 1
    nb = _NB().fit([_ngrams(c.primary_text) for c in data], [int(c.is_attack) for c in data])
    ratio = {w: nb.logp(w, 1) - nb.logp(w, 0) for w in nb.vocab
             if nb.cnt[0][w] + nb.cnt[1][w] >= 5}
    top_att = sorted(ratio, key=ratio.get, reverse=True)[:top_k]
    top_neg = sorted(ratio, key=ratio.get)[:top_k]
    acc = correct / len(data) if data else float("nan")
    return {
        "n": len(data),
        "grouped_cv_accuracy": round(acc, 4),
        "interpretation": ("HIGH lexical separability: inspect top n-grams and regenerate negatives "
                           "to mirror them" if acc > 0.9 else
                           "moderate: lexical cues exist but do not fully separate classes" if acc > 0.75 else
                           "low: classes are hard to separate from surface words alone"),
        "accuracy_by_technique": {k: round(v[0] / v[1], 4) for k, v in sorted(by_tech.items())},
        "top_attack_ngrams": top_att,
        "top_negative_ngrams": top_neg,
    }