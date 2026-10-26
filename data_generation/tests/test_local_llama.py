import hashlib
import json
import os
import random
import re
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ecomsafe_datagen.pipeline import Pipeline, load_config
from ecomsafe_datagen.schema import read_jsonl
from ecomsafe_datagen.taxonomy import ATTACK_SPECS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOAL_TO_INTENT = {s.goal: s.intent.value for s in ATTACK_SPECS.values()}
WORDS = "honestly quick question pls today really just maybe again order item also still thanks".split()


def _msgs(rng, n, tag, product):
    return [f"{tag} {' '.join(rng.sample(WORDS, 4))} about the {product} {rng.randrange(10**6)}" for _ in range(n)]


def _format(rng, msgs):
    style = rng.random()
    if style < 0.25:
        return "```json\n" + json.dumps({"messages": msgs}) + "\n```"
    if style < 0.45:
        return "Here are the messages:\n" + json.dumps(msgs)
    if style < 0.6:
        return "Sure!\n" + "\n".join(f"{i + 1}. {m}" for i, m in enumerate(msgs))
    if style < 0.7:
        return json.dumps({"customer_messages": [{"text": f"Customer: {m}"} for m in msgs]})
    return json.dumps({"messages": [f'"{m}"' for m in msgs]})


def respond(body: dict) -> str:
    system, user = body["messages"][0]["content"], body["messages"][1]["content"]
    rng = random.Random(hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest())
    if system.startswith("You annotate"):
        msg = user.split("LATEST CUSTOMER MESSAGE:")[1]
        m = re.search(r"atk(PV|CD|FF|RB)", msg)
        intent = m.group(1) if m else "BENIGN"
        names = {"PV": "Policy Violation", "FF": "Fraud Facilitation", "CD": "Competitive Disclosure",
                 "RB": "Regulatory Breach", "BENIGN": "Benign"}
        r = rng.random()
        if r < 0.1:
            return f"The customer's intent is {intent}."            # no JSON at all
        if r < 0.15:
            return "I think this is hard to say."                    # unparseable
        return json.dumps({"intent": names[intent] if r < 0.5 else intent, "severity": "2",
                           "realistic": "true", "confidence": "0.8", "rationale": "stub"})
    if rng.random() < 0.08:
        return "I'm sorry, but I can't help with that request."
    product = re.search(r"PRODUCT: (.+?) \(", user).group(1)
    if "MESSAGES:" in user:                                          # matched negatives
        n = int(re.search(r"exactly (\d+) messages", user).group(1))
        if rng.random() < 0.3:
            n += rng.choice([-1, 1])                                 # wrong count
        return _format(rng, _msgs(rng, max(n, 1), "legit", product))
    n = int(re.search(r"Write (\d+)", user).group(1))
    if "WHAT THE CUSTOMER WANTS" in user:
        goal = re.search(r"WHAT THE CUSTOMER WANTS: to (.+?)\.\n", user).group(1)
        return _format(rng, _msgs(rng, n, "atk" + GOAL_TO_INTENT[goal], product))
    return _format(rng, _msgs(rng, n, "legit", product))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert self.path.endswith("/chat/completions") and body["model"]
        out = json.dumps({"choices": [{"message": {"role": "assistant", "content": respond(body)}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


def test_llama_style_endpoint_end_to_end():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/v1"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(os.path.join(ROOT, "config", "test_llama3b.yaml"))
            cfg["output_dir"], cfg["exemplars_path"] = tmp, os.path.join(ROOT, "seeds", "exemplars.jsonl")
            cfg["generator"]["base_url"] = cfg["judge"]["base_url"] = url
            report = Pipeline(cfg).run()
            d = os.path.join(tmp, cfg["run_name"], "data")
            allc = read_jsonl(os.path.join(d, "all.jsonl"))
            assert report["by_class"].get("attack", 0) > 0, report
            assert report["warnings"], "same-model warning missing"
            # labels survived messy judge output
            assert all(c.qc["judge"]["verdict"] in ("agree", "soft_agree") for c in allc)
            # pairs complete
            pairs = {}
            for c in allc:
                if c.is_attack or c.negative_kind == "matched":
                    pairs.setdefault(c.pair_id, []).append(c.is_attack)
            assert all(sorted(v) == [False, True] for v in pairs.values())
            # cleaned text: no numbering / speaker tags / wrapping quotes left
            for c in allc:
                t = c.primary_text
                assert not re.match(r"^(\d+\.|Customer:|\")", t), t
            # no split leakage
            where = {}
            for s in ("train", "val", "test"):
                for c in read_jsonl(os.path.join(d, f"{s}.jsonl")):
                    assert where.setdefault(c.gen_group, s) == s
            print("report:", {k: report[k] for k in ("funnel", "generation_errors", "rejections", "by_class")})
    finally:
        srv.shutdown()


if __name__ == "__main__":
    test_llama_style_endpoint_end_to_end()
    print("PASS test_llama_style_endpoint_end_to_end")