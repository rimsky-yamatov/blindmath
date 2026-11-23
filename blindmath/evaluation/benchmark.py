"""Held-out reasoning benchmark (Phase 4): exact-match on freshly generated, verifiable problems.

Problems come from the same generators with a different seed; any problem whose question text also
occurs in the training split is removed so the score measures generalisation, not recall.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import defaultdict

import torch

from blindmath.data.build import REGISTRY
from blindmath.data.shards import iter_train
from blindmath.tokenizer import MathTokenizer
from blindmath.training.train import load_model, pick_device

NON_LEAN = [k for k in REGISTRY]


def build_eval_set(per_domain: int, seed: int, corpus: str | None = None) -> list[dict]:
    train_q = set()
    if corpus:
        train_q = {r.text.split("\n", 1)[0] for r in iter_train(corpus)}
    rng = random.Random(seed)
    out = []
    for dom in NON_LEAN:
        mod = REGISTRY[dom][0]
        got = 0
        for r in mod.generate(random.Random(rng.randrange(1 << 30)), per_domain * 4):
            q = r.text.split("\n", 1)[0]
            if q in train_q or "\nA: " not in r.text:
                continue
            prompt, ans = r.text.split("\nA: ", 1)
            out.append({"domain": dom, "stage": r.stage, "generator": r.generator,
                        "prompt": prompt.split("\nWork:")[0] + "\nWork:", "answer": ans.strip()})
            got += 1
            if got >= per_domain:
                break
    return out


@torch.no_grad()
def answer_of(model, tok, prompt: str, device, max_new: int = 160) -> str:
    ids = torch.tensor([tok.encode(prompt, bos=True)], device=device)
    out = model.generate(ids, max_new, temperature=0.0, stop_ids=(tok.eos_id,))
    text = tok.decode(out[0, ids.size(1):].tolist())
    if "\nA:" not in text:
        return ""
    return text.split("\nA:", 1)[1].split("\n", 1)[0].strip()


def evaluate(ckpt: str, corpus: str, per_domain: int = 50, seed: int = 999, device: str = "auto") -> dict:
    dev = pick_device(device)
    model, ck = load_model(ckpt, dev)
    tok = MathTokenizer.load(os.path.join(os.path.dirname(ckpt), ck["tokenizer"]))
    items = build_eval_set(per_domain, seed, corpus)
    hit, tot = defaultdict(int), defaultdict(int)
    for it in items:
        pred = answer_of(model, tok, it["prompt"], dev)
        key = f"{it['domain']}"
        tot[key] += 1; hit[key] += int(pred == it["answer"])
    res = {k: {"acc": hit[k] / tot[k], "n": tot[k]} for k in tot}
    res["overall"] = {"acc": sum(hit.values()) / max(1, sum(tot.values())), "n": sum(tot.values())}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--per-domain", type=int, default=50)
    ap.add_argument("--seed", type=int, default=999)
    ap.add_argument("--device", default="auto")
    a = ap.parse_args(argv)
    print(json.dumps(evaluate(a.ckpt, a.corpus, a.per_domain, a.seed, a.device), indent=2))


if __name__ == "__main__":
    main()
