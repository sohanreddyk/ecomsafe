"""
Unified record schema.

A single-turn example is just a Conversation with one user turn. Multi-turn
escalation data uses exactly the same structure, with per-turn labels, so the
per-turn probe (layer 1) and the trajectory model (layer 2) read one format.

Labels live on each USER turn (intent, severity, risk_target), because
EcomSafe scores every turn. Assistant turns are filled later by the target model
(Llama-3.2-3B / 3.1-8B) when hidden states are collected; `response_label`
(CR, COMPLIED, ...) is attached at that stage.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Iterable, Optional

SCHEMA_VERSION = "1.0"


@dataclass
class TurnLabel:
    intent: str                      # IntentLabel value
    severity: int                    # 0..3
    risk_target: float               # Eq.1 weight x severity scale
    attack_type: Optional[str] = None
    technique: Optional[str] = None
    role_in_plan: str = "attack"     # attack | setup | camouflage | benign | matched_negative | boundary
    response_label: Optional[str] = None


@dataclass
class Turn:
    role: str                        # "user" | "assistant"
    content: str
    label: Optional[TurnLabel] = None


@dataclass
class Conversation:
    conv_id: str
    turns: list[Turn]
    domain: str
    threat_class: str                # single_turn_commercial | multi_turn_escalation | benign | cross_user
    pattern: str                     # single | linear | camouflaged | late_spike | benign
    is_attack: bool
    attack_type: Optional[str]       # conversation-level attack type (None for benign)
    product: dict
    policy_topic: str
    gen_group: str                   # all variants from one LLM call share this -> never split apart
    pair_id: Optional[str] = None    # links an attack to its matched hard negative
    negative_kind: Optional[str] = None   # matched | boundary | organic
    provenance: dict = field(default_factory=dict)
    qc: dict = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    # ---- convenience ---------------------------------------------------- #
    @property
    def user_turns(self) -> list[Turn]:
        return [t for t in self.turns if t.role == "user"]

    @property
    def first_attack_turn(self) -> Optional[int]:
        """1-indexed user turn where severity first reaches >=2 (for Early Detection Rate)."""
        for i, t in enumerate(self.user_turns, 1):
            if t.label and t.label.intent != "BENIGN" and t.label.severity >= 2:
                return i
        return None

    @property
    def risk_trajectory(self) -> list[float]:
        return [t.label.risk_target if t.label else 0.0 for t in self.user_turns]

    @property
    def primary_text(self) -> str:
        """Text of the highest-risk user turn (the whole message for single-turn data)."""
        users = self.user_turns
        if not users:
            return ""
        return max(users, key=lambda t: t.label.risk_target if t.label else 0.0).content

    # ---- (de)serialization --------------------------------------------- #
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Conversation":
        d = dict(d)
        turns = []
        for t in d.pop("turns"):
            lab = t.get("label")
            turns.append(Turn(role=t["role"], content=t["content"],
                              label=TurnLabel(**lab) if lab else None))
        return cls(turns=turns, **d)


def write_jsonl(path, convs: Iterable[Conversation]) -> int:
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for c in convs:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
            n += 1
    return n


def read_jsonl(path) -> list[Conversation]:
    with open(path, encoding="utf-8") as f:
        return [Conversation.from_dict(json.loads(line)) for line in f if line.strip()]
