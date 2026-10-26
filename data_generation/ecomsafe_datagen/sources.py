"""
Adapters for external data.

1. Seed exemplars (`load_exemplars`): a JSONL of {"technique": ..., "text": ...}
   used as few-shot STYLE references in generator prompts. Populate it with
   persuasion strategies mined from tau-break/CRAFT transcripts, adversarial
   buyer personas from the negotiation papers, the Table 1 examples, and any
   real anonymized logs you are allowed to use. Exemplars are rotated so no
   single seed dominates.

2. Organic benign data (`load_bitext_csv`, `load_twitter_support_csv`): real
   customer-service messages as BENIGN records with negative_kind="organic".
   They anchor the benign distribution in real text so the probe isn't only
   learning "synthetic vs. synthetic". Each source keeps its own gen_group so
   splits stay clean, and provenance.source records the corpus for licensing.

Download the corpora yourself (Hugging Face / Kaggle) and point the config at
the local files.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import defaultdict
from typing import Optional

from .schema import Conversation, Turn, TurnLabel

# Crude keyword routing of organic messages into EcomSafe domains; anything
# unmatched is tagged "general" and excluded from per-domain metrics.
_DOMAIN_KEYWORDS = {
    "electronics": r"laptop|phone|charger|headphone|tv|monitor|camera|device|battery",
    "pharmaceuticals": r"prescription|pharmac|medic|refill|dose|pill|tablet",
    "fashion": r"shirt|dress|shoe|size|jacket|clothes|jeans|boots",
    "financial_products": r"credit card|card|payment|installment|loan|interest|insurance|charge",
    "groceries": r"grocery|groceries|produce|delivery slot|fresh|food|milk|substitut",
}


def route_domain(text: str) -> str:
    low = text.lower()
    for d, pat in _DOMAIN_KEYWORDS.items():
        if re.search(pat, low):
            return d
    return "general"


def load_exemplars(path: Optional[str]) -> dict[str, list[str]]:
    if not path:
        return {}
    out = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[r["technique"]].append(r["text"])
    return dict(out)


def rotate_exemplars(exemplars: dict[str, list[str]], rng: random.Random, n: int = 3) -> dict[str, list[str]]:
    return {k: rng.sample(v, min(n, len(v))) for k, v in exemplars.items()}


def _organic(text: str, source: str, row_id: str, extra: dict) -> Conversation:
    cid = hashlib.sha1(f"{source}|{row_id}".encode()).hexdigest()[:12]
    return Conversation(
        conv_id=f"org-{cid}",
        turns=[Turn("user", text.strip(),
                    TurnLabel(intent="BENIGN", severity=0, risk_target=0.0, role_in_plan="benign"))],
        domain=route_domain(text), threat_class="benign", pattern="single", is_attack=False,
        attack_type=None, product={}, policy_topic="", gen_group=f"org-{cid}",
        negative_kind="organic", provenance={"source": source, "row_id": row_id, **extra})


def load_bitext_csv(path: str, limit: Optional[int] = None, seed: int = 0) -> list[Conversation]:
    """Bitext customer-support dataset (columns: instruction, category, intent, ...)."""
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    random.Random(seed).shuffle(rows)
    out = []
    for i, r in enumerate(rows[:limit] if limit else rows):
        text = r.get("instruction") or r.get("utterance") or ""
        # Bitext uses {{Order Number}}-style placeholders; make them look natural.
        text = re.sub(r"\{\{[^}]+\}\}", "#48213", text)
        if text:
            out.append(_organic(text, "bitext", str(i),
                                {"category": r.get("category"), "src_intent": r.get("intent")}))
    return out


def load_twitter_support_csv(path: str, limit: Optional[int] = None, seed: int = 0) -> list[Conversation]:
    """Kaggle 'Customer Support on Twitter' (columns: tweet_id, author_id, inbound, text, ...)."""
    out = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if str(r.get("inbound", "")).lower() != "true":
                continue
            text = re.sub(r"@\w+|https?://\S+", "", r.get("text", "")).strip()
            if len(text) >= 20:
                out.append(_organic(text, "twitter_support", r.get("tweet_id", ""), {}))
    random.Random(seed).shuffle(out)
    return out[:limit] if limit else out
