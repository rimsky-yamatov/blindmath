"""Phase 5 benchmark: the model writes proofs for held-out Lean statements; Lean decides (strict acceptance).

Reports pass@1 (greedy) and pass@k (k samples) per proof family. Statements whose normalised text occurs in
the training corpus are excluded, so the score reflects generalisation.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
from collections import defaultdict

from blindmath.data.generators.lean_proofs import LeanItem, iter_items
from blindmath.data.shards import iter_train
from blindmath.reasoning.prompts import first_prompt
from blindmath.theorem.lean_runner import LeanRunner

_NAME = re.compile(r"\b[A-Za-z_]+\d{1,6}(?:_[A-Za-z]+)?\b")


def norm(text: str) -> str:
    return _NAME.sub("NAME", " ".join(text.split()))


def train_statements(corpus: str) -> set[str]:
    out = set()
    for r in iter_train(corpus):
        if r.domain == "lean_proofs" and "\nA: " in r.text:
            out.add(norm(r.text[len("Q: Lean4\n"):].split("\nA: ", 1)[0]))
    return out


def build_set(n: int, seed: int, corpus: str | None) -> list[LeanItem]:
    seen = train_statements(corpus) if corpus else set()
    out = []
    for it in iter_items(random.Random(seed), n * 6):
        if norm(it.prompt()) in seen:
            continue
        out.append(it)
        if len(out) >= n:
            break
    return out


def evaluate(ckpt: str, corpus: str, n: int = 60, k: int = 4, temperature: float = 0.7, seed: int = 4242,
             device: str = "auto") -> dict:
    from blindmath.reasoning.search import ModelProposer
    from blindmath.tokenizer import MathTokenizer
    from blindmath.training.train import load_model, pick_device
    runner = LeanRunner()
    if not runner.available:
        raise SystemExit("Lean 4 is required for this benchmark")
    dev = pick_device(device)
    model, ck = load_model(ckpt, dev)
    tok = MathTokenizer.load(os.path.join(os.path.dirname(ckpt), ck["tokenizer"]))
    prop = ModelProposer(model, tok, dev)
    items = build_set(n, seed, corpus)
    p1, pk, tot = defaultdict(int), defaultdict(int), defaultdict(int)
    for it in items:
        prompt = first_prompt(it.prelude, it.header)
        greedy = prop.complete(prompt, 1, temperature=0.0)[0]
        ok1 = runner.verify_proof(it.prelude, it.header, greedy).accepted
        okk = ok1
        if not okk:
            for cand in prop.complete(prompt, k, temperature=temperature):
                if runner.verify_proof(it.prelude, it.header, cand).accepted:
                    okk = True; break
        tot[it.family] += 1; p1[it.family] += int(ok1); pk[it.family] += int(okk)
    res = {f: {"pass@1": p1[f] / tot[f], f"pass@{k}": pk[f] / tot[f], "n": tot[f]} for f in tot}
    N = sum(tot.values())
    res["overall"] = {"pass@1": sum(p1.values()) / max(1, N), f"pass@{k}": sum(pk.values()) / max(1, N), "n": N}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--device", default="auto")
    a = ap.parse_args(argv)
    print(json.dumps(evaluate(a.ckpt, a.corpus, a.n, a.k, seed=a.seed, device=a.device), indent=2))


if __name__ == "__main__":
    main()
