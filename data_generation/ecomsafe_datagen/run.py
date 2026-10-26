"""CLI.

  python -m ecomsafe_datagen.run --config config/single_turn.yaml
  python -m ecomsafe_datagen.run --config config/single_turn.yaml --backend mock --attack-target 200
  python -m ecomsafe_datagen.run check --config config/single_turn.yaml [--smoke]
  python -m ecomsafe_datagen.run --config config/single_turn.yaml \
      --gen-backend local_llama --gen-model meta-llama/Llama-3.2-3B-Instruct --gen-url http://localhost:8000/v1 \
      --judge-backend grok --judge-model grok-4.3                      # swap roles without editing YAML
  python -m ecomsafe_datagen.run annotate --data runs/<run>/data/all.jsonl --n 300
  python -m ecomsafe_datagen.run score --annotations filled.csv --key runs/<run>/annotation_key.csv
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from .annotate import export_blind_sample, score_annotations
from .envfile import load_env
from .llm import BACKENDS, QuotaExhaustedError
from .pipeline import Pipeline, load_config
from .schema import read_jsonl


def _add_run_args(ap: argparse.ArgumentParser):
    ap.add_argument("--config", required=True)
    ap.add_argument("--backend", choices=BACKENDS,
                    help="override generator AND judge backend (use 'mock' for a dry run)")
    for role, flag in (("generator", "gen"), ("judge", "judge")):
        ap.add_argument(f"--{flag}-backend", choices=BACKENDS, help=f"override {role} backend")
        ap.add_argument(f"--{flag}-model", help=f"override {role} model")
        ap.add_argument(f"--{flag}-url", help=f"override {role} base_url")
    ap.add_argument("--attack-target", type=int)
    ap.add_argument("--run-name")


def _apply_overrides(cfg: dict, a) -> dict:
    if a.backend:
        cfg["generator"]["backend"] = cfg["judge"]["backend"] = a.backend
        if a.backend == "mock":
            cfg["generator"]["model"], cfg["judge"]["model"] = "mock-gen", "mock-judge"
    for role, flag in (("generator", "gen"), ("judge", "judge")):
        for key in ("backend", "model", "url"):
            v = getattr(a, f"{flag}_{key}")
            if v:
                cfg[role]["base_url" if key == "url" else key] = v
    if a.attack_target:
        cfg["single_turn"]["attack_target"] = a.attack_target
    if a.run_name:
        cfg["run_name"] = a.run_name
    return cfg


def _pop_env_file(argv: list) -> list:
    """Handle the optional global --env-file PATH flag, then load .env (keys only, never printed)."""
    explicit = None
    if "--env-file" in argv:
        i = argv.index("--env-file")
        explicit = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:]
    path = load_env(explicit)
    if path:
        print(f"[env] loaded keys from {path}")
    return argv


def main(argv=None):
    argv = _pop_env_file(list(sys.argv[1:] if argv is None else argv))
    if argv and argv[0] == "annotate":
        ap = argparse.ArgumentParser()
        ap.add_argument("--data", required=True)
        ap.add_argument("--n", type=int, default=300)
        a = ap.parse_args(argv[1:])
        d = os.path.dirname(os.path.dirname(a.data))
        n = export_blind_sample(read_jsonl(a.data), a.n, os.path.join(d, "annotation_blind.csv"),
                                os.path.join(d, "annotation_key.csv"))
        print(f"exported {n} items to {d}")
        return
    if argv and argv[0] == "score":
        ap = argparse.ArgumentParser()
        ap.add_argument("--annotations", required=True)
        ap.add_argument("--key", required=True)
        a = ap.parse_args(argv[1:])
        print(json.dumps(score_annotations(a.annotations, a.key), indent=2))
        return
    if argv and argv[0] == "check":
        from .preflight import run_check
        ap = argparse.ArgumentParser()
        _add_run_args(ap)
        ap.add_argument("--smoke", action="store_true", help="also run a ~10-attack end-to-end pipeline")
        a = ap.parse_args(argv[1:])
        ok = run_check(_apply_overrides(load_config(a.config), a), smoke=a.smoke)
        sys.exit(0 if ok else 1)

    ap = argparse.ArgumentParser()
    _add_run_args(ap)
    a = ap.parse_args(argv)
    try:
        Pipeline(_apply_overrides(load_config(a.config), a)).run()
    except QuotaExhaustedError as e:
        print(f"\n[stopped] {e}\n"
              "A provider quota is used up (usually the daily limit). Everything that finished is cached:\n"
              "rerun the SAME command after the quota resets and it continues from here at no extra cost.")
        sys.exit(2)


if __name__ == "__main__":
    main()