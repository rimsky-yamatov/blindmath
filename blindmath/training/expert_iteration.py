"""Self-play data (expert iteration): the model proposes proofs, Lean verifies, verified ones become training data.

Only strictly accepted proofs are kept, and they are tagged source="self_play:<checkpoint>" so the origin of
every training record stays auditable (rule 2). Output is a JSONL consumable by `train --extra-train`.
"""
from __future__ import annotations

import argparse
import json
import os
import random

from blindmath.data import audit
from blindmath.data.generators.common import rec
from blindmath.data.generators.lean_proofs import iter_items
from blindmath.reasoning.prompts import first_prompt
from blindmath.theorem.lean_runner import LeanRunner


def collect(ckpt: str, out_path: str, n: int = 400, k: int = 4, temperature: float = 0.8, seed: int = 777,
            device: str = "auto") -> dict:
    from blindmath.reasoning.search import ModelProposer
    from blindmath.tokenizer import MathTokenizer
    from blindmath.training.train import load_model, pick_device
    runner = LeanRunner()
    dev = pick_device(device)
    model, ck = load_model(ckpt, dev)
    tok = MathTokenizer.load(os.path.join(os.path.dirname(ckpt), ck["tokenizer"]))
    prop = ModelProposer(model, tok, dev)
    kept, tried, seen = 0, 0, set()
    with open(out_path, "w", encoding="utf-8") as f:
        for it in iter_items(random.Random(seed), n):
            tried += 1
            prompt = first_prompt(it.prelude, it.header)
            cands = prop.complete(prompt, 1, temperature=0.0) + prop.complete(prompt, k, temperature=temperature)
            for cand in cands:
                if cand in seen and False:
                    continue
                if runner.verify_proof(it.prelude, it.header, cand).accepted:
                    text = f"Q: Lean4\n{it.prompt()}\nA: {cand.strip()}\n"
                    if audit.audit_text(text):
                        break
                    r = rec("lean_proofs", f"self_play_{it.family}", text, it.stage, kind="proof")
                    r.source = f"self_play:{os.path.basename(ckpt)}"
                    f.write(r.to_json() + "\n"); kept += 1
                    break
    return {"statements": tried, "verified_kept": kept, "out": out_path}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out", default="data/corpus/self_play.jsonl")
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--seed", type=int, default=777)
    ap.add_argument("--device", default="auto")
    a = ap.parse_args(argv)
    print(json.dumps(collect(a.ckpt, a.out, a.n, a.k, seed=a.seed, device=a.device)))


if __name__ == "__main__":
    main()
