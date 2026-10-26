"""
Realizer: turns ConversationPlans into Conversations.

Single-turn: one call returns k variants -> k Conversations sharing a gen_group.
Matched negatives: one call per attack batch, aligned 1:1 -> each pair shares a
pair_id (and the attack's gen_group, so pairs and batches stay in one split).
Multi-turn: turns are realized sequentially, each conditioned on the history.
Assistant turns are optional here (an `agent_sim` client can fill placeholder
replies); the final assistant turns come from the target model at hidden-state
collection time.
"""
from __future__ import annotations

import random
import re
import threading
from collections import Counter
from typing import Optional, Sequence

from .llm import LLMClient, LLMRequest, extract_messages
from .plans import ConversationPlan, TurnSpec
from .prompts import (GENERATOR_SYSTEM, PROMPT_VERSION, attack_prompt, benign_turn_prompt,
                      boundary_prompt, matched_negative_prompt, repair_negative_prompt)
from .schema import Conversation, Turn, TurnLabel
from .taxonomy import risk_target

_REFUSAL = re.compile(r"^\s*(i[’']?m sorry|i can(?:no|[’'])t|i won[’']?t|as an ai|i am unable)", re.I)


class GenerationError(RuntimeError):
    pass


def _label(ts: TurnSpec) -> TurnLabel:
    return TurnLabel(intent=ts.intent.value, severity=ts.severity, risk_target=risk_target(ts.intent, ts.severity),
                     attack_type=ts.attack_type.value if ts.attack_type else None,
                     technique=ts.technique, role_in_plan=ts.role_in_plan)


class Realizer:
    def __init__(self, gen: LLMClient, k: int = 5, temperature: float = 0.9,
                 exemplars: Optional[dict[str, list[str]]] = None, agent_sim: Optional[LLMClient] = None,
                 retries: int = 2, max_tokens: int = 1500):
        self.gen, self.k, self.temperature = gen, k, temperature
        self.retries, self.max_tokens = retries, max_tokens
        self.refusals: Counter = Counter()      # (attack_type, technique) -> refused attempts
        self.attempts: Counter = Counter()      # (attack_type, technique) -> all attempts
        self._lock = threading.Lock()
        self.exemplars = exemplars or {}          # technique -> seed messages (e.g. mined from tau-break)
        self.agent_sim = agent_sim

    # ---- low level ------------------------------------------------------ #
    def _rotate(self, technique: str, key: str, n: int = 3) -> list[str]:
        """Different exemplars per plan so no single seed dominates the style."""
        pool = self.exemplars.get(technique, [])
        return random.Random(key).sample(pool, min(n, len(pool)))

    def _messages(self, prompt: str, task: str, meta: dict, n_expected: int) -> list[str]:
        """Call the generator; on refusal / unparseable / wrong count, re-sample with a new seed."""
        err = "unparseable_output"
        for attempt in range(self.retries + 1):
            raw = self.gen.complete(LLMRequest(GENERATOR_SYSTEM, prompt, task, meta, self.temperature,
                                               max_tokens=self.max_tokens, seed=attempt))
            cell = (meta.get("attack_type"), meta.get("technique")) if task == "generate_attack" else None
            refused = bool(_REFUSAL.search(raw))
            if cell:
                with self._lock:
                    self.attempts[cell] += 1
                    self.refusals[cell] += refused
            if refused:
                err = "generator_refusal"
                continue
            msgs = extract_messages(raw)
            if not msgs:
                err = "unparseable_output"
                continue
            if task == "generate_negative" and len(msgs) != n_expected:
                err = "negative_count_mismatch"
                continue
            return msgs[:n_expected]
        raise GenerationError(err)

    def _provenance(self, plan: ConversationPlan, task: str) -> dict:
        return {"generator": self.gen.model, "prompt_version": PROMPT_VERSION, "task": task,
                "plan_id": plan.plan_id, "source": "synthetic"}

    def _conv(self, plan: ConversationPlan, turns: list[Turn], idx: int, task: str,
              gen_group: str, pair_id: Optional[str] = None) -> Conversation:
        return Conversation(
            conv_id=f"{plan.plan_id}-{idx}", turns=turns, domain=plan.domain,
            threat_class=plan.threat_class, pattern=plan.pattern, is_attack=plan.is_attack,
            attack_type=plan.attack_type.value if plan.attack_type else None,
            product=plan.product, policy_topic=plan.policy_topic, gen_group=gen_group,
            pair_id=pair_id, negative_kind=plan.negative_kind,
            provenance=self._provenance(plan, task))

    # ---- single-turn ---------------------------------------------------- #
    def realize_single(self, plan: ConversationPlan) -> list[Conversation]:
        assert plan.n_turns == 1
        ts = plan.turns[0]
        meta = {"k": self.k, "attack_type": ts.attack_type.value, "technique": ts.technique,
                "product": plan.product["name"], "domain": plan.domain}
        prompt = attack_prompt(plan, ts, self.k, exemplars=self._rotate(ts.technique, plan.plan_id))
        msgs = self._messages(prompt, "generate_attack", meta, self.k)
        return [self._conv(plan, [Turn("user", m, _label(ts))], i, "generate_attack",
                           gen_group=plan.plan_id, pair_id=f"{plan.plan_id}-{i}")
                for i, m in enumerate(msgs)]

    def realize_matched_negatives(self, neg_plan: ConversationPlan,
                                  attacks: Sequence[Conversation]) -> list[Conversation]:
        """One legit counterpart per attack, in order; falls back to one call per attack
        if the model keeps returning the wrong number of messages."""
        texts = [a.primary_text for a in attacks]
        meta = {"k": len(texts), "product": neg_plan.product["name"], "domain": neg_plan.domain}
        try:
            msgs: list[Optional[str]] = list(self._messages(
                matched_negative_prompt(neg_plan, texts), "generate_negative", meta, len(texts)))
        except GenerationError:
            # Any failure of a multi-message batch (wrong count, refusal, bad JSON) falls back
            # to one call per attack: one hard message should not sink the whole batch.
            if len(texts) == 1:
                raise
            msgs = []
            for t in texts:
                try:
                    msgs.append(self._messages(matched_negative_prompt(neg_plan, [t]), "generate_negative",
                                               {**meta, "k": 1}, 1)[0])
                except GenerationError:
                    msgs.append(None)
        ts = neg_plan.turns[0]
        out = []
        for a, m in zip(attacks, msgs):
            if m is None:
                continue
            out.append(self._conv(neg_plan, [Turn("user", m, _label(ts))], int(a.conv_id.rsplit("-", 1)[1]),
                                  "generate_negative", gen_group=a.gen_group, pair_id=a.pair_id))
        return out

    def repair_negative(self, neg: Conversation, attack_text: str, reason: str) -> str:
        """New text for a matched negative the judge rejected (the judge's reason is the feedback)."""
        prompt = repair_negative_prompt(neg, attack_text, neg.primary_text, reason)
        meta = {"k": 1, "product": neg.product.get("name", ""), "domain": neg.domain}
        return self._messages(prompt, "repair_negative", meta, 1)[0]

    def realize_boundary(self, plan: ConversationPlan) -> list[Conversation]:
        ts = plan.turns[0]
        meta = {"k": self.k, "product": plan.product["name"], "domain": plan.domain}
        msgs = self._messages(boundary_prompt(plan, self.k), "generate_boundary", meta, self.k)
        return [self._conv(plan, [Turn("user", m, _label(ts))], i, "generate_boundary", gen_group=plan.plan_id)
                for i, m in enumerate(msgs)]

    # ---- multi-turn (Threat Class 2) ------------------------------------ #
    def realize_multi(self, plan: ConversationPlan) -> Conversation:
        history: list[tuple[str, str]] = []
        turns: list[Turn] = []
        for ts in plan.turns:
            meta = {"k": 1, "attack_type": ts.attack_type.value if ts.attack_type else None,
                    "technique": ts.technique, "product": plan.product["name"], "domain": plan.domain}
            if ts.intent.value == "BENIGN":
                msg = self._messages(benign_turn_prompt(plan, ts, 1, history), "generate_benign", meta, 1)[0]
            else:
                msg = self._messages(attack_prompt(plan, ts, 1, history,
                                                   self._rotate(ts.technique, plan.plan_id + str(len(turns)))),
                                     "generate_attack", meta, 1)[0]
            turns.append(Turn("user", msg, _label(ts)))
            history.append(("user", msg))
            if self.agent_sim is not None:
                transcript = "\n".join(f"{r.upper()}: {c}" for r, c in history)
                reply = self.agent_sim.complete(LLMRequest(
                    "You are a helpful shopping assistant that follows store policy. "
                    "Reply to the customer's latest message.", transcript,
                    "agent_sim", {"n_history": len(history)}, temperature=0.3))
                turns.append(Turn("assistant", reply))
                history.append(("assistant", reply))
        return self._conv(plan, turns, 0, "generate_multi", gen_group=plan.plan_id)
