"""Shared helpers for running Llama locally (Hugging Face transformers, Apple MPS).

Used by scripts/llama_scratch.py (the from-scratch pipeline). Reads no project data.

- load_llama(): tokenizer + fp16 model on MPS (CPU fallback).
- LlamaJSON.call(): one chat request that must return a JSON object, with
  automatic checks, deterministic per-attempt seeds, retries, and a JSONL log
  of every attempt.
- register helpers and form checks for single customer messages.
"""

import hashlib
import json
import re
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL = "meta-llama/Llama-3.2-3B-Instruct"

INTENT_WORDS = re.compile(r"\b(fraud\w*|scam\w*|cheat\w*|trick\w*|lie|lying|steal\w*|get away with|scheme|con the|fool you)\b", re.I)
DOSE = re.compile(r"\b\d+\s*(mg|mcg|ml|milligram\w*|tablets? (a|per) day)\b|\btimes (a|per) day\b|\bevery \d+ hours\b|"
                  r"\b(per|a) day for\b|\bdos(e|es|age|ing)\b|\btitrat\w*", re.I)
# Real consumer brands the 3B model tends to reach for; the spec forbids real brand names.
BRANDS = re.compile(r"\b(samsung|iphone|sony|lg|nike|adidas|gucci|prada|tylenol|advil|walmart|amazon|costco|"
                    r"best buy|visa|mastercard|paypal|klarna|affirm|afterpay)\b", re.I)
STRENGTH = re.compile(r"\s*\b\d+(\.\d+)?\s*(mg|mcg|ml|g|iu)\b", re.I)
# Failures that may never be kept, however many attempts it takes.
HARD = ("doses", "real brand")
REFUSAL = re.compile(r"\b(I can(no|')t (help|assist|create|write|provide)|as an AI|I'm not able to (help|create|write)|I won't)\b", re.I)


def ntok(s):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9',]*[A-Za-z0-9]|[A-Za-z0-9]", s))


def ngrams(text, n=6):
    w = re.findall(r"[a-z0-9$]+", text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def parse_json(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def load_llama(model_name=DEFAULT_MODEL):
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.float16).to(device).eval()
    return tok, model, device


class LlamaJSON:
    def __init__(self, model_name, log_path, temperature=0.8, top_p=0.9, cache_path=None):
        self.model_name = model_name
        # Resume support: each finished call's result is appended to the cache, keyed by
        # call key, and reused on a rerun instead of calling the model again.
        self.cache_path = Path(cache_path) if cache_path else None
        self.cache = {}
        if self.cache_path and self.cache_path.exists():
            for line in self.cache_path.read_text().splitlines():
                if line.strip():
                    c = json.loads(line)
                    self.cache[c["key"]] = (c["obj"], c["fails"], c["attempt"])
        self.tok, self.model, self.device = load_llama(model_name)
        self.temperature, self.top_p = temperature, top_p
        self.log = Path(log_path)
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.stats = {"calls": 0, "attempts": 0, "json_failures": 0, "kept_with_failures": 0, "seconds": 0.0}

    def _generate(self, messages, seed, max_new_tokens, temperature):
        enc = self.tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=True)
        ids, attn = enc["input_ids"].to(self.device), enc["attention_mask"].to(self.device)
        torch.manual_seed(seed)
        with torch.no_grad():
            out = self.model.generate(input_ids=ids, attention_mask=attn, do_sample=True,
                                      temperature=temperature, top_p=self.top_p,
                                      max_new_tokens=max_new_tokens, pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)

    def call(self, key, system, user, check, max_attempts=5, max_new_tokens=400, temperature=None, feedback=True,
             hard_limit=14):
        """Return (obj, fails, attempt). check(obj) -> list of failure strings ([] = pass).

        On failure, the next attempt gets a short note naming the failed checks
        (feedback=True), which is how a human would iterate with the model.
        """
        t0 = time.time()
        self.stats["calls"] += 1
        if key in self.cache:
            self.stats["cached"] = self.stats.get("cached", 0) + 1
            return self.cache[key]
        best = None
        notes = ""
        with self.log.open("a") as log:
            attempt = 0
            while True:
                attempt += 1
                # Past max_attempts, keep going only while no attempt is free of hard (safety) failures.
                if attempt > max_attempts and (best is not None or attempt > hard_limit):
                    break
                seed = int(hashlib.sha256(f"{key}-{attempt}".encode()).hexdigest()[:8], 16)
                msgs = [{"role": "system", "content": system},
                        {"role": "user", "content": user + notes}]
                raw = self._generate(msgs, seed, max_new_tokens, temperature or self.temperature)
                obj = parse_json(raw)
                fails = ["json"] if obj is None else check(obj)
                self.stats["attempts"] += 1
                if obj is None:
                    self.stats["json_failures"] += 1
                log.write(json.dumps({"key": key, "attempt": attempt, "seed": seed, "fails": fails, "raw": raw}) + "\n")
                hard = any(h in f for f in fails for h in HARD)
                if obj is not None and not hard and (best is None or len(fails) < len(best[1])):
                    best = (obj, fails, attempt)
                if not fails:
                    break
                if feedback and fails != ["json"]:
                    notes = ("\n\nYour previous answer failed these checks: " + "; ".join(fails[:6]) +
                             ". Fix them and answer again with JSON only.")
                elif feedback:
                    notes = "\n\nYour previous answer was not valid JSON. Answer with one JSON object only."
        self.stats["seconds"] += time.time() - t0
        result = (None, ["json or safety"], attempt) if best is None else best
        if best is not None and best[1]:
            self.stats["kept_with_failures"] += 1
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("a") as f:
                f.write(json.dumps({"key": key, "obj": result[0], "fails": result[1], "attempt": result[2]}) + "\n")
            self.cache[key] = result
        return result


# ---------------------------------------------------------------- register

def describe_register(reg):
    bits = ["starts lowercase, mostly lowercase, casual" if reg["casing"] == "lower" else "normal sentence capitalisation",
            "a question" if reg["act"] == "Q" else "a request or instruction with no question mark anywhere",
            ("ends with '?'" if reg["act"] == "Q" else "ends with '.'") if reg["end_punct"] else "no punctuation at the very end",
            f"about {reg['tokens']} words",
            "opens with a greeting" if reg["greeting"] else "no greeting"]
    if reg["please"]:
        bits.append("polite (please / could you)")
    return "; ".join(bits)


def check_message(text, reg, role):
    """Form checks for one customer message against its register spec."""
    fails = []
    if not isinstance(text, str) or len(text.strip()) < 15:
        return [f"{role}: message missing or too short"]
    text = text.strip()
    if re.search(r"(^|\n)\s*(agent|assistant|customer)\s*:", text, re.I) or "\n" in text:
        fails.append(f"{role}: must be one message with no speaker labels")
    if REFUSAL.search(text):
        fails.append(f"{role}: refusal text")
    if INTENT_WORDS.search(text):
        fails.append(f"{role}: must not state intent to cheat")
    if DOSE.search(text):
        fails.append(f"{role}: must not mention doses or medical guidance")
    if BRANDS.search(text):
        fails.append(f"{role}: must not use a real brand name")
    if (len(re.findall(r"[.?!]+(\s|$)", text)) or 1) > 4:
        fails.append(f"{role}: too many sentences")
    if text[:1].islower() != (reg["casing"] == "lower"):
        fails.append(f"{role}: casing should be {'lowercase' if reg['casing'] == 'lower' else 'normal capitalisation'}")
    if ("?" in text) != (reg["act"] == "Q"):
        fails.append(f"{role}: should be {'a question' if reg['act'] == 'Q' else 'a request with no question mark'}")
    if (text[-1:] in ".?!") != reg["end_punct"]:
        fails.append(f"{role}: end punctuation should be {'present' if reg['end_punct'] else 'absent'}")
    if abs(ntok(text) / reg["tokens"] - 1) > 0.40:
        fails.append(f"{role}: length should be about {reg['tokens']} words (was {ntok(text)})")
    return fails


def sanitize_product(name):
    """Strip real brand words and medicine strengths from a product reference.

    Product names are chosen by the model in the design phase; the spec forbids real
    brand names and any dosing detail, so these are removed deterministically
    (e.g. "Samsung 4K TV" -> "4K TV", "Acetaminophen 500mg" -> "Acetaminophen"); manufacturer
    model numbers are removed too."""
    out = STRENGTH.sub("", BRANDS.sub("", name))
    out = re.sub(r"\b[A-Z]{1,3}\d{2,}[A-Z]*\b", "", out)  # manufacturer model numbers such as X850E
    out = re.sub(r"\s{2,}", " ", out).strip(" -,")
    return out[:1].upper() + out[1:] if out else "product"


def scrub_text(text):
    """Remove real brand words, medicine strengths, and model numbers from free text
    (design scenarios), keeping the rest of the sentence."""
    out = STRENGTH.sub("", BRANDS.sub("", text))
    out = re.sub(r"\b[A-Z]{1,3}\d{2,}[A-Z]*\b", "", out)
    return re.sub(r"\s{2,}", " ", out).replace(" ,", ",").replace(" .", ".").strip()
