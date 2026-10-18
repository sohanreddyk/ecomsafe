"""
Conversation plans.

A plan is the label-side blueprint of a conversation: one TurnSpec per user turn
(intent, severity, technique, role). Labels are decided BEFORE any text is
generated, so ground truth comes from the design, and the LLM only realizes
text for it. The judge stage then checks that the realized text matches.

Single-turn data = plans of length 1. The multi-turn builders below
(linear / camouflaged / late_spike) produce plans of length N with the same
TurnSpec type, so the realizer, judge, splitter and writer need no changes when
you move to Threat Class 2.
"""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field, replace
from typing import Optional

from .domains import DOMAINS, DomainSpec
from .taxonomy import ATTACK_SPECS, TECHNIQUES, AttackType, IntentLabel


@dataclass(frozen=True)
class TurnSpec:
    intent: IntentLabel
    severity: int
    attack_type: Optional[AttackType] = None
    technique: Optional[str] = None
    role_in_plan: str = "attack"
    note: str = ""            # free-text steering for this turn (used by multi-turn plans)


@dataclass
class ConversationPlan:
    plan_id: str
    domain: str
    product: dict
    policy_topic: str
    threat_class: str
    pattern: str
    turns: list[TurnSpec]
    is_attack: bool
    attack_type: Optional[AttackType] = None
    negative_kind: Optional[str] = None
    negative_technique: Optional[str] = None   # framing reused by a matched negative
    meta: dict = field(default_factory=dict)

    @property
    def n_turns(self) -> int:
        return len(self.turns)


def _pid(*parts) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:12]


def _pick_topic(domain: DomainSpec, attack: AttackType, rng: random.Random) -> str:
    topic = ATTACK_SPECS[attack].policy_topic
    # Policy bypass also targets warranty / cancellation rules where they exist.
    if attack == AttackType.POLICY_BYPASS and domain.policies.get("warranty") and rng.random() < 0.3:
        topic = "warranty"
    return topic


# --------------------------------------------------------------------------- #
# Single-turn builders (Threat Class 1)
# --------------------------------------------------------------------------- #
def single_turn_attack(domain: str, attack: AttackType, technique: str, severity: int,
                       rng: random.Random, idx: int = 0) -> ConversationPlan:
    d = DOMAINS[domain]
    spec = ATTACK_SPECS[attack]
    return ConversationPlan(
        plan_id=_pid("st", domain, attack.value, technique, severity, idx),
        domain=domain,
        product=rng.choice(d.products),
        policy_topic=_pick_topic(d, attack, rng),
        threat_class="single_turn_commercial",
        pattern="single",
        turns=[TurnSpec(spec.intent, severity, attack, technique, "attack")],
        is_attack=True,
        attack_type=attack,
    )


def matched_negative(attack_plan: ConversationPlan, keep_framing: bool) -> ConversationPlan:
    """Same domain/product/policy topic as the attack, legitimate intent.

    keep_framing=True reuses the attack's framing technique in benign form, so
    framing (role-play, authority claims, ...) is NOT a shortcut feature for the
    probe: it must look at intent.
    """
    tech = attack_plan.turns[-1].technique if keep_framing else "direct"
    return replace(
        attack_plan,
        plan_id=attack_plan.plan_id + "-neg",
        threat_class="benign",
        turns=[TurnSpec(IntentLabel.BENIGN, 0, attack_plan.attack_type, tech, "matched_negative")],
        is_attack=False,
        negative_kind="matched",
        negative_technique=tech,
    )


def boundary_plan(domain: str, attack: AttackType, rng: random.Random, idx: int = 0) -> ConversationPlan:
    d = DOMAINS[domain]
    return ConversationPlan(
        plan_id=_pid("bd", domain, attack.value, idx),
        domain=domain,
        product=rng.choice(d.products),
        policy_topic=_pick_topic(d, attack, rng),
        threat_class="benign",
        pattern="single",
        turns=[TurnSpec(IntentLabel.BENIGN, 0, attack, "direct", "boundary")],
        is_attack=False,
        attack_type=attack,
        negative_kind="boundary",
    )


# --------------------------------------------------------------------------- #
# Multi-turn builders (Threat Class 2) - same TurnSpec type, longer plans.
# Realization is supported by generate.Realizer; tune prompts in a later step.
# --------------------------------------------------------------------------- #
def _benign_turn(attack: AttackType, note: str, role: str = "setup") -> TurnSpec:
    return TurnSpec(IntentLabel.BENIGN, 0, attack, "direct", role, note)


def linear_escalation(domain: str, attack: AttackType, technique: str, n_turns: int,
                      rng: random.Random, idx: int = 0) -> ConversationPlan:
    """Monotonically increasing severity: 0 -> ... -> 3."""
    spec = ATTACK_SPECS[attack]
    turns = [_benign_turn(attack, "ordinary shopping question about the product")]
    mid = n_turns - 2
    for i in range(mid):
        sev = 1 if i < mid / 2 else 2
        turns.append(TurnSpec(spec.intent, sev, attack, "direct" if sev == 1 else technique,
                              "attack", "move one step closer to the goal than the previous turn"))
    turns.append(TurnSpec(spec.intent, 3, attack, technique, "attack", "make the explicit ask"))
    return _mt_plan("linear", domain, attack, turns, rng, idx)


def late_spike(domain: str, attack: AttackType, technique: str, n_turns: int,
               rng: random.Random, idx: int = 0) -> ConversationPlan:
    """Several fully benign turns, then a single high-risk exploit."""
    spec = ATTACK_SPECS[attack]
    turns = [_benign_turn(attack, "ordinary, friendly shopping/service question") for _ in range(n_turns - 1)]
    turns.append(TurnSpec(spec.intent, 3, attack, technique, "attack", "sudden explicit ask"))
    return _mt_plan("late_spike", domain, attack, turns, rng, idx)


def camouflaged_escalation(domain: str, attack: AttackType, technique: str, n_turns: int,
                           rng: random.Random, idx: int = 0) -> ConversationPlan:
    """Risky turns interleaved with benign 'camouflage' turns (targets sigma_t)."""
    spec = ATTACK_SPECS[attack]
    turns = [_benign_turn(attack, "ordinary shopping question")]
    sev = 1
    for i in range(1, n_turns):
        if i == n_turns - 1:
            turns.append(TurnSpec(spec.intent, 3, attack, technique, "attack", "explicit ask"))
        elif i % 2 == 0:
            turns.append(_benign_turn(attack, "unrelated harmless question to reset suspicion", "camouflage"))
        else:
            turns.append(TurnSpec(spec.intent, sev, attack, technique if sev >= 2 else "direct",
                                  "attack", "probe further"))
            sev = min(sev + 1, 2)
    return _mt_plan("camouflaged", domain, attack, turns, rng, idx)


MULTI_TURN_BUILDERS = {
    "linear": linear_escalation,
    "late_spike": late_spike,
    "camouflaged": camouflaged_escalation,
}


def _mt_plan(pattern, domain, attack, turns, rng, idx) -> ConversationPlan:
    d = DOMAINS[domain]
    return ConversationPlan(
        plan_id=_pid("mt", pattern, domain, attack.value, idx),
        domain=domain, product=rng.choice(d.products),
        policy_topic=_pick_topic(d, attack, rng),
        threat_class="multi_turn_escalation", pattern=pattern, turns=turns,
        is_attack=True, attack_type=attack,
    )


# --------------------------------------------------------------------------- #
# Stratified sampling
# --------------------------------------------------------------------------- #
def allocate(total: int, weights: dict) -> dict:
    """Largest-remainder allocation of an integer budget to weighted cells."""
    w_sum = sum(weights.values())
    if w_sum <= 0 or total <= 0:
        return {k: 0 for k in weights}
    raw = {k: total * w / w_sum for k, w in weights.items()}
    out = {k: math.floor(v) for k, v in raw.items()}
    rem = total - sum(out.values())
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[:rem]:
        out[k] += 1
    return out

def allocate_or_sample(total: int, weights: dict, rng: random.Random) -> dict:
    """Integer budget per cell.

    When the budget covers every cell, use deterministic largest-remainder allocation.
    When it is smaller than the number of cells (small pilot or smoke runs), largest
    remainder would hand everything to the few highest-weight cells, so instead draw
    distinct cells at random in proportion to their weights (Efraimidis-Spirakis).
    """
    live = {k: w for k, w in weights.items() if w > 0}
    if total >= len(live):
        return allocate(total, live)
    keys = sorted(live, key=lambda k: rng.random() ** (1.0 / live[k]), reverse=True)
    chosen = set(keys[:total])
    return {k: int(k in chosen) for k in live}

def sample_single_turn_plans(n_calls: int, domains: list[str], techniques: list[str],
                             severity_mix: dict[int, float], rng: random.Random) -> list[ConversationPlan]:
    """Grid over domain x attack (weighted by domain compatibility) x technique (uniform)."""
    cells = {}
    for dom in domains:
        for at, w in DOMAINS[dom].attack_weights.items():
            if w > 0:
                for tech in techniques:
                    cells[(dom, at, tech)] = w
    counts = allocate_or_sample(n_calls, cells, rng)
    sev_levels, sev_w = zip(*severity_mix.items())
    plans, idx = [], 0
    for (dom, at, tech), n in counts.items():
        for _ in range(n):
            sev = rng.choices(sev_levels, sev_w)[0]
            plans.append(single_turn_attack(dom, at, tech, sev, rng, idx))
            idx += 1
    rng.shuffle(plans)
    return plans


def sample_boundary_plans(n_calls: int, domains: list[str], rng: random.Random) -> list[ConversationPlan]:
    cells = {(dom, at): w for dom in domains for at, w in DOMAINS[dom].attack_weights.items() if w > 0}
    plans, idx = [], 0
    for (dom, at), n in allocate_or_sample(n_calls, cells, rng).items():
        for _ in range(n):
            plans.append(boundary_plan(dom, at, rng, idx))
            idx += 1
    return plans


def sample_multi_turn_plans(n: int, domains: list[str], techniques: list[str],
                            pattern_mix: dict[str, float], turn_range: tuple[int, int],
                            rng: random.Random) -> list[ConversationPlan]:
    """For the Threat Class 2 stage. Included now so the config/pipeline contract is fixed."""
    plans = []
    patterns, pw = zip(*pattern_mix.items())
    cells = [(dom, at) for dom in domains for at, w in DOMAINS[dom].attack_weights.items() if w > 0]
    for i in range(n):
        dom, at = rng.choice(cells)
        builder = MULTI_TURN_BUILDERS[rng.choices(patterns, pw)[0]]
        plans.append(builder(dom, at, rng.choice(techniques), rng.randint(*turn_range), rng, i))
    return plans


def all_techniques() -> list[str]:
    return list(TECHNIQUES)
