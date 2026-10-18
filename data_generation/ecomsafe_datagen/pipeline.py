"""
EcomSafeBench data pipeline.

  plan -> generate attacks -> matched negatives -> boundary cases -> organic benign
       -> rule filter -> near-dup filter -> blind judge (+ negative repair) -> pair integrity
       -> stratified trim -> splits (+ held-out splits) -> audits -> write

Each stage records what it dropped and why (rejected.jsonl), so the dataset
section of the paper can report the full funnel. All LLM calls are cached, so a
re-run after a crash or a config tweak only pays for new calls.

Multi-turn plug-in: set multi_turn.enabled=true. The same filter / judge / split
/ write stages run on those conversations unchanged.
"""
from __future__ import annotations

import json
import math
import os
import random
import statistics
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import yaml

from .domains import DOMAINS
from .generate import GenerationError, Realizer
from .llm import QUOTA_EXHAUSTED, QuotaExhaustedError, build_client, model_family
from .plans import (allocate, all_techniques, matched_negative, sample_boundary_plans,
                    sample_multi_turn_plans, sample_single_turn_plans)
from .prompts import PROMPT_VERSION
from .quality import BlindJudge, NearDupFilter, RuleFilter, shortcut_audit
from .taxonomy import AttackType
from .schema import SCHEMA_VERSION, Conversation, write_jsonl
from .sources import load_bitext_csv, load_exemplars, load_twitter_support_csv
from .splits import grouped_split, holdout_split


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def refusal_rates(realizer) -> dict:
    """'refused/attempts (pct)' per attack type and per technique."""
    out = {}
    for name, idx in (("by_attack_type", 0), ("by_technique", 1)):
        ref, att = Counter(), Counter()
        for cell, n in realizer.attempts.items():
            att[cell[idx]] += n
            ref[cell[idx]] += realizer.refusals[cell]
        out[name] = {k: f"{ref[k]}/{att[k]} ({ref[k] / att[k]:.0%})" for k in sorted(att, key=str)}
    return out


def independence_warnings(cfg: dict) -> list[str]:
    g, j = cfg["generator"], cfg["judge"]
    if g.get("model") == j.get("model"):
        return ["generator and judge are the same model: judge agreement is not an independent check "
                "(fine for a test run, not for the benchmark)"]
    fg, fj = model_family(g.get("backend"), g.get("model")), model_family(j.get("backend"), j.get("model"))
    if fg == fj and fg != "mock":
        return [f"generator and judge are both {fg}-family models: they may share blind spots, so report "
                "human-vs-judge agreement and consider a cross-family spot check"]
    return []


class Pipeline:
    def __init__(self, cfg: dict):
        QUOTA_EXHAUSTED.clear()                     # a new run starts with a clean quota state
        self.cfg = cfg
        self.rng = random.Random(cfg.get("seed", 0))
        self.run_dir = os.path.join(cfg.get("output_dir", "runs"), cfg["run_name"])
        os.makedirs(self.run_dir, exist_ok=True)
        cache = os.path.join(cfg.get("output_dir", "runs"), "llm_cache.sqlite")
        self.gen = build_client(cfg["generator"], cache)
        self.judge_client = build_client(cfg["judge"], cache)
        self.realizer = Realizer(self.gen, k=cfg["generator"].get("variants_per_call", 5),
                                 temperature=cfg["generator"].get("temperature", 0.9),
                                 exemplars=load_exemplars(cfg.get("exemplars_path")),
                                 retries=cfg["generator"].get("retries", 2),
                                 max_tokens=cfg["generator"].get("max_tokens", 1500))
        self.warnings: list[str] = independence_warnings(cfg)
        for w in self.warnings:
            print(f"[warning] {w}")
        self.workers = cfg["generator"].get("max_workers", 8)
        self.rejected: list[Conversation] = []
        self.funnel: list[tuple[str, int]] = []
        self.gen_errors: Counter = Counter()

    # ------------------------------------------------------------------ #
    def _pmap(self, fn: Callable, items: list, label: str) -> list:
        def safe(x):
            try:
                return fn(x)
            except GenerationError as e:
                self.gen_errors[f"{label}:{e}"] += 1
                return None
            except QuotaExhaustedError:
                raise                                    # stop the run cleanly (see run.py)
            except Exception as e:  # noqa: BLE001 - provider outages, timeouts after all retries
                self.gen_errors[f"{label}:error_{type(e).__name__}"] += 1
                return None
        t0 = time.time()
        with ThreadPoolExecutor(self.workers) as ex:
            out = list(ex.map(safe, items))
        print(f"[{label}] {len(items)} calls in {time.time() - t0:.1f}s, "
              f"{sum(o is None for o in out)} failed")
        return out

    def _reject(self, convs: list[Conversation], reason: str, stage: str):
        for c in convs:
            c.qc.setdefault("rejected", {"stage": stage, "reason": reason})
            self.rejected.append(c)

    def _log(self, stage: str, convs: list[Conversation]):
        self.funnel.append((stage, len(convs)))
        print(f"  {stage:<28} {len(convs):>6}")

    # ------------------------------------------------------------------ #
    def generate_single_turn(self) -> list[Conversation]:
        st = self.cfg["single_turn"]
        k = self.realizer.k
        domains = st.get("domains") or list(DOMAINS)
        techniques = st.get("techniques") or all_techniques()
        if techniques == "all":
            techniques = all_techniques()
        sev_mix = {int(a): float(b) for a, b in st.get("severity_mix", {2: 0.5, 3: 0.5}).items()}
        n_calls = math.ceil(st["attack_target"] * st.get("overgenerate", 1.4) / k)
        plans = sample_single_turn_plans(n_calls, domains, techniques, sev_mix, self.rng)

        attack_batches = self._pmap(self.realizer.realize_single, plans, "attacks")
        attacks = [c for b in attack_batches if b for c in b]

        convs = list(attacks)
        if st.get("matched_negatives", True):
            match_rate = st.get("negative_framing_match_rate", 0.5)
            jobs = []
            for plan, batch in zip(plans, attack_batches):
                if batch:
                    jobs.append((matched_negative(plan, keep_framing=self.rng.random() < match_rate), batch))
            neg_batches = self._pmap(lambda j: self.realizer.realize_matched_negatives(*j), jobs, "negatives")
            convs += [c for b in neg_batches if b for c in b]

        n_bound = math.ceil(st["attack_target"] * st.get("boundary_ratio", 0.25) / k)
        if n_bound:
            bplans = sample_boundary_plans(n_bound, domains, self.rng)
            convs += [c for b in self._pmap(self.realizer.realize_boundary, bplans, "boundary") if b for c in b]
        return convs

    def generate_multi_turn(self) -> list[Conversation]:
        mt = self.cfg.get("multi_turn", {})
        if not mt.get("enabled"):
            return []
        plans = sample_multi_turn_plans(
            mt["n_conversations"], mt.get("domains") or list(DOMAINS),
            mt.get("techniques") or all_techniques(), mt["pattern_mix"],
            tuple(mt.get("turn_range", [3, 7])), self.rng)
        return [c for c in self._pmap(self.realizer.realize_multi, plans, "multi_turn") if c]

    def load_organic(self) -> list[Conversation]:
        org = self.cfg.get("organic") or {}
        out = []
        if org.get("bitext_csv"):
            out += load_bitext_csv(org["bitext_csv"], org.get("limit"), self.cfg.get("seed", 0))
        if org.get("twitter_csv"):
            out += load_twitter_support_csv(org["twitter_csv"], org.get("limit"), self.cfg.get("seed", 0))
        return out

    # ------------------------------------------------------------------ #
    def quality(self, convs: list[Conversation]) -> list[Conversation]:
        q = self.cfg.get("quality", {})
        rf = self._rules = RuleFilter(q.get("min_chars", 15), q.get("max_chars", 700))
        kept = []
        for c in convs:
            r = rf.reasons(c)
            (self._reject([c], ",".join(r), "rules") if r else kept.append(c))
        self._log("after rule filter", kept)

        dd = NearDupFilter(q.get("dedup_threshold", 0.8), seed=self.cfg.get("seed", 0))
        out = []
        # per class: minimal pairs (attack vs its negative) must survive dedup
        for key in ("attack", "matched", "boundary", "organic"):
            part = [c for c in kept if (("attack" if c.is_attack else c.negative_kind) == key)]
            k, dropped = dd.filter(part)
            out += k
            for c, of in dropped:
                self._reject([c], f"near_dup_of:{of}", "dedup")
        self._log("after near-dup filter", out)

        jc = self.cfg["judge"]
        judge = BlindJudge(self.judge_client, [tuple(p) for p in jc.get("soft_confusions", [["PV", "FF"]])],
                           jc.get("min_confidence", 0.5), jc.get("require_realistic", True),
                           jc.get("max_workers", self.workers), jc.get("retries", 1))
        judge.judge(out, turns=jc.get("turns", "attack_turns"))
        accept = {"agree"} | ({"soft_agree"} if jc.get("accept_soft_agree", True) else set())
        self._repair_negatives(out, judge, accept, jc.get("repair_rounds", 2), jc.get("turns", "attack_turns"))
        final = []
        for c in out:
            v = c.qc["judge"]["verdict"]
            (final.append(c) if v in accept else self._reject([c], v, "judge"))
        self._log("after blind judge (+repair)", final)
        return self._pair_integrity(final)

    def _repair_negatives(self, convs, judge, accept, rounds: int, turns: str):
        """Generate-verify-repair for matched negatives.

        A matched negative the judge labeled as a violation is rewritten using the judge's
        rationale as feedback, then judged again (up to `rounds` times). Only negatives whose
        attack was accepted are repaired. Repaired records keep their history in
        qc['repair_history'] and are counted in the report: they were optimized to pass this
        judge, so human annotation is the independent check for them.
        """
        self.repair_stats = Counter()
        if not rounds:
            return
        attacks = {c.pair_id: c for c in convs if c.is_attack and c.pair_id}
        for rnd in range(1, rounds + 1):
            todo = [c for c in convs if c.negative_kind == "matched" and c.qc["judge"]["verdict"] == "disagree"
                    and c.pair_id in attacks and attacks[c.pair_id].qc["judge"]["verdict"] in accept]
            if not todo:
                break

            def fix(c):
                t = c.qc["judge"]["turns"][-1]
                reason = t.get("rationale") or f"it was labeled {t.get('intent')}"
                return self.realizer.repair_negative(c, attacks[c.pair_id].primary_text, reason)

            texts = self._pmap(fix, todo, f"repair round {rnd}")
            rewritten = []
            for c, text in zip(todo, texts):
                if not text:
                    continue
                old, t = c.turns[0].content, c.qc["judge"]["turns"][-1]
                c.turns[0].content = text
                if self._rules.reasons(c):                 # repaired text must pass the rule filter too
                    c.turns[0].content = old
                    continue
                c.qc.setdefault("repair_history", []).append(
                    {"round": rnd, "text": old, "judge_intent": t.get("intent"), "reason": t.get("rationale")})
                c.qc["repairs"] = rnd
                rewritten.append(c)
            self.repair_stats["attempted"] += len(todo)
            if rewritten:
                judge.judge(rewritten, turns=turns)
            self.repair_stats["fixed"] += sum(c.qc["judge"]["verdict"] in accept for c in rewritten)
        print(f"  negative repair: {self.repair_stats['fixed']} fixed of {self.repair_stats['attempted']} attempts")

    def _pair_integrity(self, convs: list[Conversation]) -> list[Conversation]:
        if self.cfg["single_turn"].get("keep_orphans", False):
            return convs
        by_pair = defaultdict(list)
        for c in convs:
            if c.pair_id and (c.is_attack or c.negative_kind == "matched"):
                by_pair[c.pair_id].append(c)
        orphan_ids = {c.conv_id for p in by_pair.values() if len(p) == 1 for c in p}
        out = [c for c in convs if c.conv_id not in orphan_ids]
        self._reject([c for c in convs if c.conv_id in orphan_ids], "pair_orphan", "pairing")
        self._log("after pair integrity", out)
        return out

    def trim(self, convs: list[Conversation]) -> list[Conversation]:
        """Cap single-turn attacks to attack_target, preserving the design distribution."""
        st = self.cfg["single_turn"]
        attacks = [c for c in convs if c.is_attack and c.pattern == "single"]
        target = st["attack_target"]
        if len(attacks) <= target:
            return convs
        cells = defaultdict(list)
        for c in attacks:
            cells[(c.domain, c.attack_type)].append(c)
        weights = {k: DOMAINS[k[0]].attack_weights[AttackType(k[1])] for k in cells}
        quota = allocate(target, weights)
        drop_pairs = set()
        for key, items in cells.items():
            self.rng.shuffle(items)
            for c in items[quota[key]:]:
                drop_pairs.add(c.pair_id)
        out = [c for c in convs if not (c.pair_id in drop_pairs and (c.is_attack or c.negative_kind == "matched"))]
        self._log("after stratified trim", out)
        return out

    # ------------------------------------------------------------------ #
    def run(self) -> dict:
        print(f"== EcomSafe datagen: {self.cfg['run_name']} ==")
        convs = self.generate_single_turn() + self.generate_multi_turn() + self.load_organic()
        self._log("generated", convs)
        convs = self.trim(self.quality(convs))

        sp = self.cfg.get("splits", {})
        splits = grouped_split(convs, sp.get("ratios", {"train": .7, "val": .1, "test": .2}), self.cfg.get("seed", 0))
        data_dir = os.path.join(self.run_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        write_jsonl(os.path.join(data_dir, "all.jsonl"), convs)
        for name, part in splits.items():
            write_jsonl(os.path.join(data_dir, f"{name}.jsonl"), part)
        for h in sp.get("holdouts", []):
            hs = holdout_split(convs, h["field"], h["value"], seed=self.cfg.get("seed", 0))
            hdir = os.path.join(data_dir, f"holdout_{h['field']}_{h['value']}")
            os.makedirs(hdir, exist_ok=True)
            for name, part in hs.items():
                write_jsonl(os.path.join(hdir, f"{name}.jsonl"), part)
        write_jsonl(os.path.join(self.run_dir, "rejected.jsonl"), self.rejected)

        report = self.report(convs, splits)
        with open(os.path.join(self.run_dir, "report.json"), "w") as f:
            json.dump(report, f, indent=2)
        with open(os.path.join(self.run_dir, "config_used.yaml"), "w") as f:
            yaml.safe_dump(self.cfg, f, sort_keys=False)
        with open(os.path.join(self.run_dir, "report.md"), "w") as f:
            f.write(render_markdown(report))
        print(f"done -> {self.run_dir}")
        return report

    def report(self, convs, splits) -> dict:
        def cnt(f):
            return dict(Counter(f(c) for c in convs))
        cell = defaultdict(Counter)
        for c in convs:
            if c.is_attack:
                cell[c.domain][c.attack_type] += 1
        lens = [len(c.primary_text.split()) for c in convs]
        return {
            "run_name": self.cfg["run_name"], "schema_version": SCHEMA_VERSION, "prompt_version": PROMPT_VERSION,
            "generator": self.gen.model, "judge": self.judge_client.model,
            "warnings": self.warnings,
            "funnel": self.funnel,
            "generation_errors": dict(self.gen_errors),
            "refusal_rates": refusal_rates(self.realizer),
            "negative_repair": dict(getattr(self, "repair_stats", {})),
            "rejections": dict(Counter(f"{c.qc['rejected']['stage']}:{c.qc['rejected']['reason'].split(':')[0]}"
                                       for c in self.rejected)),
            "by_class": cnt(lambda c: "attack" if c.is_attack else f"benign/{c.negative_kind}"),
            "by_domain": cnt(lambda c: c.domain),
            "attack_domain_x_type": {d: dict(v) for d, v in cell.items()},
            "attack_by_technique": dict(Counter(c.user_turns[-1].label.technique for c in convs if c.is_attack)),
            "judge_verdicts_kept": cnt(lambda c: c.qc.get("judge", {}).get("verdict")),
            "words_per_message": {"mean": round(statistics.mean(lens), 1) if lens else 0,
                                  "median": statistics.median(lens) if lens else 0},
            "splits": {k: len(v) for k, v in splits.items()},
            "shortcut_audit": shortcut_audit(convs, seed=self.cfg.get("seed", 0)),
            "cache": {"hits": getattr(self.gen, "hits", None), "misses": getattr(self.gen, "misses", None)},
        }


def render_markdown(r: dict) -> str:
    lines = [f"# EcomSafeBench data report: {r['run_name']}", "",
             f"Generator: `{r['generator']}` | Judge: `{r['judge']}` | prompts `{r['prompt_version']}`", "",
             *[f"> **Warning:** {w}" for w in r.get("warnings", [])], "",
             "## Funnel", "", "| stage | n |", "|---|---|"]
    lines += [f"| {s} | {n} |" for s, n in r["funnel"]]
    lines += ["", "## Composition", "", f"By class: {r['by_class']}", "", f"Splits: {r['splits']}", "",
              "## Attacks: domain x type", ""]
    types = sorted({t for v in r["attack_domain_x_type"].values() for t in v})
    lines += ["| domain | " + " | ".join(types) + " |", "|---" * (len(types) + 1) + "|"]
    for d, v in sorted(r["attack_domain_x_type"].items()):
        lines.append(f"| {d} | " + " | ".join(str(v.get(t, 0)) for t in types) + " |")
    a = r["shortcut_audit"]
    lines += ["", "## Shortcut audit (attack vs matched negative, bag-of-ngrams NB, grouped CV)", "",
              f"Accuracy: **{a['grouped_cv_accuracy']}** ({a['interpretation']})", "",
              f"By technique: {a['accuracy_by_technique']}", "",
              f"Top attack n-grams: {', '.join(a['top_attack_ngrams'][:15])}", "",
              f"Top negative n-grams: {', '.join(a['top_negative_ngrams'][:15])}", "",
              "## Rejections", "", f"{r['rejections']}", "", f"Generation errors: {r['generation_errors']}", "",
              f"Matched-negative repair: {r.get('negative_repair', {})}", "",
              "## Generator refusals (all attempts, including ones rescued by a retry)", "",
              f"By attack type: {r['refusal_rates']['by_attack_type']}", "",
              f"By technique: {r['refusal_rates']['by_technique']}", ""]
    return "\n".join(lines)