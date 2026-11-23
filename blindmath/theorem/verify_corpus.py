"""Sample Lean records from the built corpus and compile them with Lean (corpus-level quality check)."""
from __future__ import annotations

import argparse
import os
import random

from blindmath.data.shards import iter_train
from blindmath.theorem.lean_runner import LeanRunner


def source_of(text: str) -> str | None:
    if not text.startswith("Q: Lean4\n") or "\nTry:" in text:
        return None
    body = text[len("Q: Lean4\n"):]
    stmt, proof = body.split("\nA: ", 1)
    return stmt.rstrip() + " " + proof.strip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    recs = [r for r in iter_train(a.corpus) if r.domain == "lean_proofs"]
    rng = random.Random(a.seed)
    sample = [s for s in (source_of(r.text) for r in rng.sample(recs, min(a.n, len(recs)))) if s]
    runner = LeanRunner(timeout=300)
    bad = 0
    for i in range(0, len(sample), 40):
        part = sample[i:i + 40]
        if runner.check_source("\n\n".join(part)).accepted:
            continue
        for s in part:                       # duplicate names in a chunk or a real failure: check singly
            if not runner.check_source(s).accepted:
                bad += 1; print("FAIL", s[:120].replace("\n", " "))
    print(f"checked {len(sample)} corpus Lean records, {bad} failures")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
