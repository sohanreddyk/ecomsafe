"""Validate a policy file (default Llama/policy/ecomsafe_policy_llama.md) and report clause statistics.

Checks:
1. Format: every clause header matches `### P-NNN | Category | source: S`,
   S is one of ABCD-guidelines / ABCD-ontology / authored, IDs are unique
   and sequential, and each clause has a violation predicate and checkable line.
2. Verbatim copying: flags any run of N consecutive words (default 6) shared
   between a clause body and any ABCD guideline string. The ABCD licence
   permits copying, but the project rule is to paraphrase and attribute.
3. Statistics: clause counts by category and by source.

Usage:  python scripts/check_policy.py [--policy ...] [--abcd-dir ...] [--ngram 6]
Exit code is non-zero if any format error or verbatim overlap is found.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HEADER = re.compile(r"^### (P-\d{3}) \| ([^|]+?) \| source: (\S+)\s*$")
SOURCES = {"ABCD-guidelines", "ABCD-ontology", "authored"}


def parse_clauses(text):
    clauses, cur = [], None
    for line in text.splitlines():
        m = HEADER.match(line)
        if m:
            cur = {"id": m[1], "category": m[2].strip(), "source": m[3], "body": []}
            clauses.append(cur)
        elif line.startswith("## ") or line.startswith("---"):
            cur = None
        elif cur is not None:
            cur["body"].append(line)
    return clauses


def words(s):
    return re.findall(r"[a-z0-9$]+", s.lower())


def guideline_strings(guidelines):
    for flow in guidelines.values():
        yield flow["description"]
        for sf in flow["subflows"].values():
            yield from sf["instructions"]
            for step in sf["actions"]:
                yield step.get("text", "")
                yield from step.get("subtext", [])


def ngrams(ws, n):
    return {tuple(ws[i : i + n]) for i in range(len(ws) - n + 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="Llama/policy/ecomsafe_policy_llama.md")
    ap.add_argument("--abcd-dir", default="data/abcd")
    ap.add_argument("--ngram", type=int, default=6)
    args = ap.parse_args()

    clauses = parse_clauses(Path(args.policy).read_text())
    errors = []
    for i, c in enumerate(clauses, 1):
        if c["id"] != f"P-{i:03d}":
            errors.append(f"{c['id']}: expected P-{i:03d} (non-sequential)")
        if c["source"] not in SOURCES:
            errors.append(f"{c['id']}: unknown source {c['source']!r}")
        body = "\n".join(c["body"])
        if "- violation predicate:" not in body:
            errors.append(f"{c['id']}: missing violation predicate")
        if "- checkable:" not in body:
            errors.append(f"{c['id']}: missing checkable line")

    guidelines = json.loads((Path(args.abcd_dir) / "guidelines.json").read_text())
    src_grams = set()
    for s in guideline_strings(guidelines):
        src_grams |= ngrams(words(s), args.ngram)
    overlaps = []
    for c in clauses:
        hit = ngrams(words("\n".join(c["body"])), args.ngram) & src_grams
        if hit:
            overlaps.append((c["id"], sorted(" ".join(g) for g in hit)))

    print(f"clauses: {len(clauses)}")
    print("\nby category:")
    for k, v in Counter(c["category"] for c in clauses).items():
        print(f"  {k:16s} {v}")
    print("\nby source:")
    for k, v in sorted(Counter(c["source"] for c in clauses).items()):
        print(f"  {k:16s} {v}")
    print("\ncategory x source:")
    cs = Counter((c["category"], c["source"]) for c in clauses)
    for (cat, src), v in cs.items():
        print(f"  {cat:16s} {src:16s} {v}")

    print(f"\nformat errors: {len(errors)}")
    for e in errors:
        print("  " + e)
    print(f"verbatim {args.ngram}-gram overlaps with ABCD guidelines: {len(overlaps)}")
    for cid, grams in overlaps:
        print(f"  {cid}: {grams}")
    sys.exit(1 if errors or overlaps else 0)


if __name__ == "__main__":
    main()
