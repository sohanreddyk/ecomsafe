"""Offline tests (mock backend). Run: python -m pytest -q  (or python tests/test_pipeline.py)"""
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ecomsafe_datagen.generate import Realizer
from ecomsafe_datagen.llm import MockClient
from ecomsafe_datagen.pipeline import Pipeline, load_config
from ecomsafe_datagen.plans import sample_multi_turn_plans
from ecomsafe_datagen.schema import Conversation, read_jsonl
from ecomsafe_datagen.splits import components, grouped_split, holdout_split
from ecomsafe_datagen.taxonomy import RISK_WEIGHTS, IntentLabel, risk_target

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "config", "single_turn.yaml")


def _run(tmp, **over):
    cfg = load_config(CFG)
    cfg["output_dir"], cfg["run_name"] = tmp, "t"
    cfg["exemplars_path"] = os.path.join(ROOT, "seeds", "exemplars.jsonl")  # independent of the working directory
    cfg["generator"].update(backend="mock", model="mock-gen")
    cfg["judge"].update(backend="mock", model="mock-judge")
    cfg["single_turn"]["attack_target"] = 150
    cfg.update(over)
    Pipeline(cfg).run()
    return os.path.join(tmp, "t", "data")


def test_risk_target_matches_eq1():
    assert risk_target(IntentLabel.FF, 3) == RISK_WEIGHTS[IntentLabel.FF] == 1.0
    assert risk_target(IntentLabel.CD, 3) == 0.4
    assert risk_target(IntentLabel.BENIGN, 3) == 0.0


def test_no_group_or_pair_leakage_across_splits():
    with tempfile.TemporaryDirectory() as tmp:
        d = _run(tmp)
        where = {}
        for split in ("train", "val", "test"):
            for c in read_jsonl(os.path.join(d, f"{split}.jsonl")):
                for key in (f"g:{c.gen_group}", f"p:{c.pair_id}" if c.pair_id else None):
                    if key:
                        assert where.setdefault(key, split) == split, f"{key} leaks across splits"


def test_pairs_are_complete_and_matched():
    with tempfile.TemporaryDirectory() as tmp:
        allc = read_jsonl(os.path.join(_run(tmp), "all.jsonl"))
        pairs = {}
        for c in allc:
            if c.is_attack or c.negative_kind == "matched":
                pairs.setdefault(c.pair_id, []).append(c)
        for pid, ps in pairs.items():
            assert len(ps) == 2 and {p.is_attack for p in ps} == {True, False}, pid
            a, n = sorted(ps, key=lambda p: not p.is_attack)
            assert a.product == n.product and a.policy_topic == n.policy_topic


def test_holdout_domain_is_disjoint():
    with tempfile.TemporaryDirectory() as tmp:
        allc = read_jsonl(os.path.join(_run(tmp), "all.jsonl"))
        hs = holdout_split(allc, "domain", "groceries")
        assert all(c.domain != "groceries" for c in hs["train"] + hs["val"])
        assert any(c.domain == "groceries" for c in hs["test"])


def test_multi_turn_uses_same_schema():
    r = Realizer(MockClient("mock-gen"), k=1)
    plans = sample_multi_turn_plans(10, ["electronics", "groceries"], ["direct", "persona_override"],
                                    {"linear": 1, "camouflaged": 1, "late_spike": 1}, (3, 6), random.Random(0))
    for p in plans:
        try:
            c = r.realize_multi(p)
        except Exception:
            continue  # mock refusals
        c2 = Conversation.from_dict(c.to_dict())
        assert len(c2.user_turns) == p.n_turns
        assert c2.first_attack_turn is not None
        assert c2.risk_trajectory[-1] > 0
        if p.pattern == "late_spike":
            assert all(x == 0 for x in c2.risk_trajectory[:-1])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
