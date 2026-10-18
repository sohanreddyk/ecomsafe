import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT, HERE]

import test_local_llama as llama_stub  # noqa: E402
from ecomsafe_datagen.llm import (GeminiClient, GrokClient, GroqClient, LLMRequest, LocalLlamaClient,  # noqa: E402
                                  RateLimiter, build_client, resolve_role)
from ecomsafe_datagen.pipeline import independence_warnings, load_config  # noqa: E402
from ecomsafe_datagen.preflight import run_check  # noqa: E402
from ecomsafe_datagen.run import _add_run_args, _apply_overrides  # noqa: E402

KEYS = {"grok": "xai-test", "gemini": "gm-test", "groq": "gsk-test"}
MODELS = {"local_llama": "meta-llama/Llama-3.2-3B-Instruct", "grok": "grok-4.3", "gemini": "gemini-2.5-flash",
          "groq": "openai/gpt-oss-120b"}
os.environ.update(XAI_API_KEY=KEYS["grok"], GEMINI_API_KEY=KEYS["gemini"], GROQ_API_KEY=KEYS["groq"])

# stub judge recognizes the pre-flight check's fixed violation sentence
_orig = llama_stub.respond


def _respond(body):
    u = body["messages"][1]["content"]
    if "approve a full refund on my Vexa laptop" in u:
        body = json.loads(json.dumps(body))
        body["messages"][1]["content"] = u.replace("approve a full refund", "atkPV approve a full refund")
    return _orig(body)


def make_handler(name, key, models, prefix, reject, list_prefix=""):
    state = {"429_sent": 0, "rejected": 0}

    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj, headers=None):
            out = json.dumps(obj).encode()
            self.send_response(code)
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)

        def _ok(self):
            if not self.path.startswith(prefix):
                self._send(404, {"error": "wrong path"})
                return False
            if key and self.headers.get("Authorization") != f"Bearer {key}":
                self._send(401, {"error": "bad key"})
                return False
            return True

        def do_GET(self):
            if self._ok() and self.path.endswith("/models"):
                self._send(200, {"data": [{"id": list_prefix + m} for m in models]})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if not self._ok():
                return
            if body["model"] not in models:
                return self._send(404, {"error": f"model {body['model']} not found"})
            if name == "groq" and "llama" in body["model"] and "reasoning_effort" in body:
                state["rejected"] += 1
                return self._send(400, {"error": "`reasoning_effort` is not supported with this model"})
            if reject in body:
                state["rejected"] += 1
                return self._send(400, {"error": f"unsupported: {reject}"})
            if name == "gemini" and state["429_sent"] == 0:
                state["429_sent"] += 1
                return self._send(429, {"error": "quota"}, {"Retry-After": "0"})
            self._send(200, {"choices": [{"message": {"content": _respond(body)}}],
                             "usage": {"prompt_tokens": 500, "completion_tokens": 200}})

        def log_message(self, *a):
            pass
    return H, state


@contextlib.contextmanager
def stubs():
    specs = {
        "local_llama": (None, [MODELS["local_llama"]], "/v1", "__none__", ""),
        "grok": (KEYS["grok"], ["grok-4.3", "grok-4.5"], "/v1", "seed", ""),
        "gemini": (KEYS["gemini"], ["gemini-2.5-flash", "gemini-3-flash"], "/v1beta/openai", "response_format", "models/"),
        "groq": (KEYS["groq"], ["openai/gpt-oss-120b", "llama-3.1-8b-instant"], "/openai/v1", "__none__", ""),
    }
    servers, urls, states = [], {}, {}
    for name, (key, models, prefix, reject, lp) in specs.items():
        H, st = make_handler(name, key, models, prefix, reject, lp)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        urls[name] = f"http://127.0.0.1:{srv.server_address[1]}{prefix}"
        states[name] = st
    try:
        yield urls, states
    finally:
        for s in servers:
            s.shutdown()


def _cfg(tmp, gen, judge, urls):
    """single_turn.yaml with ONLY backend + model changed (+ stub URLs)."""
    cfg = load_config(os.path.join(ROOT, "config", "single_turn.yaml"))
    cfg["output_dir"], cfg["exemplars_path"] = tmp, os.path.join(ROOT, "seeds", "exemplars.jsonl")
    for role, b in (("generator", gen), ("judge", judge)):
        cfg[role]["backend"], cfg[role]["model"] = b, MODELS[b]
        cfg[role]["base_url"] = urls[b]
        cfg[role]["requests_per_minute"] = 6000      # keep the test fast; real default for gemini is 10
        cfg[role]["tokens_per_minute"] = 10 ** 9
    cfg["single_turn"]["attack_target"] = 20
    return cfg


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


# --------------------------------------------------------------------------- #
def test_defaults_fill_in_from_backend_and_model_only():
    for b, url, env, cls in [("local_llama", "http://localhost:8000/v1", None, LocalLlamaClient),
                             ("grok", "https://api.x.ai/v1", "XAI_API_KEY", GrokClient),
                             ("gemini", "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY",
                              GeminiClient), ("groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", GroqClient)]:
        r = resolve_role({"backend": b, "model": MODELS[b]})
        assert r["base_url"] == url and r.get("api_key_env") == env, r
        c = build_client({"backend": b, "model": MODELS[b]}, cache_path=None)
        assert type(c) is cls and c.base_url == url
    assert resolve_role({"backend": "gemini", "model": "g"})["requests_per_minute"] == 10
    g = resolve_role({"backend": "groq", "model": "x"})
    assert (g["requests_per_minute"], g["tokens_per_minute"], g["limit_per_model"]) == (30, 6000, True)


def test_every_generator_judge_pair_works():
    backends = ["local_llama", "grok", "gemini", "groq"]
    with stubs() as (urls, states), tempfile.TemporaryDirectory() as tmp:
        for gen in backends:
            for judge in backends:
                ok, out = _quiet(run_check, _cfg(tmp, gen, judge, urls))
                assert ok, f"{gen} -> {judge}\n{out}"
                same = gen == judge
                assert ("!! ] config  generator/judge independence" in out) == same, out
        assert states["grok"]["rejected"] > 0 and states["gemini"]["rejected"] > 0   # param-drop path ran
        assert states["gemini"]["429_sent"] == 1                                     # 429 path ran


def test_smoke_gemini_generator_grok_judge():
    with stubs() as (urls, _), tempfile.TemporaryDirectory() as tmp:
        ok, out = _quiet(run_check, _cfg(tmp, "gemini", "grok", urls), smoke=True)
        assert ok and "XX" not in out, out


def test_unknown_model_lists_available_models():
    with stubs() as (urls, _), tempfile.TemporaryDirectory() as tmp:
        cfg = _cfg(tmp, "gemini", "local_llama", urls)
        cfg["generator"]["model"] = "gemini-nope"
        ok, out = _quiet(run_check, cfg)
        assert not ok and "gemini-3-flash" in out and "models/" not in out, out


def test_missing_keys_fail_cleanly():
    with stubs() as (urls, _), tempfile.TemporaryDirectory() as tmp:
        for b, env in (("grok", "XAI_API_KEY"), ("gemini", "GEMINI_API_KEY"), ("groq", "GROQ_API_KEY")):
            saved = os.environ.pop(env)
            ok, out = _quiet(run_check, _cfg(tmp, b, "local_llama", urls))
            os.environ[env] = saved
            assert not ok and f"{env}=..." in out, out


def test_rate_limiter_spaces_requests_and_is_shared():
    with stubs() as (urls, _):
        a = build_client({"backend": "local_llama", "model": MODELS["local_llama"], "base_url": urls["local_llama"],
                          "requests_per_minute": 120}, None)
        b = build_client({"backend": "local_llama", "model": MODELS["local_llama"], "base_url": urls["local_llama"],
                          "requests_per_minute": 120}, None)
        assert a.limiter is b.limiter, "same provider+key must share one quota"
        req = LLMRequest("You annotate x", "LATEST CUSTOMER MESSAGE: hi", "judge")
        t0 = time.monotonic()
        for c in (a, b, a):
            c.complete(req)
        assert time.monotonic() - t0 >= 0.9   # 3 calls at 2/s

def test_groq_switch_to_llama_model_drops_reasoning_effort():
    with stubs() as (urls, states):
        c = build_client({"backend": "groq", "model": "llama-3.1-8b-instant", "base_url": urls["groq"],
                          "extra_params": {"reasoning_effort": "low"}, "tokens_per_minute": 10 ** 9}, None)
        out = c.complete(LLMRequest("You annotate x", "LATEST CUSTOMER MESSAGE: hi", "judge"))
        assert out and "reasoning_effort" in c.dropped and states["groq"]["rejected"] == 1


def test_groq_token_budget_and_per_model_quotas():
    lim = RateLimiter(30, 6000)
    assert abs(lim.interval(900) - 9.0) < 1e-9 and abs(lim.interval(10) - 2.0) < 1e-9
    a = build_client({"backend": "groq", "model": "openai/gpt-oss-120b"}, None)
    b = build_client({"backend": "groq", "model": "llama-3.1-8b-instant"}, None)
    c = build_client({"backend": "groq", "model": "openai/gpt-oss-120b"}, None)
    assert a.limiter is c.limiter and a.limiter is not b.limiter

def test_cli_override_swaps_roles():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = load_config(os.path.join(ROOT, "config", "single_turn.yaml"))
        ap = argparse.ArgumentParser()
        _add_run_args(ap)
        a = ap.parse_args(["--config", "x", "--gen-backend", "gemini", "--gen-model", "gemini-2.5-flash",
                           "--judge-backend", "grok", "--judge-model", "grok-4.3"])
        sw = _apply_overrides(cfg, a)
        assert (sw["generator"]["backend"], sw["judge"]["backend"]) == ("gemini", "grok")
        assert independence_warnings(sw) == []


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)