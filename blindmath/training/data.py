"""Token streams from the corpus: tokenise once, sample documents by curriculum weight, pack to seq_len."""
from __future__ import annotations

import random
from array import array
from collections import defaultdict

import torch

from blindmath.data.schema import read_jsonl
from blindmath.tokenizer import MathTokenizer


class TokenizedCorpus:
    def __init__(self, path: str, tok: MathTokenizer, max_len: int):
        self.by_stage: dict[int, list[array]] = defaultdict(list)   # compact storage for 10^6 documents
        code = "H" if tok.vocab_size < 65536 else "I"
        self.eos = tok.eos_id
        for r in read_jsonl(path):
            ids = tok.encode(r.text, bos=True, eos=True)
            if len(ids) <= max_len + 1:
                self.by_stage[r.stage].append(array(code, ids))
        self.n_docs = sum(len(v) for v in self.by_stage.values())
        assert self.n_docs, f"no documents in {path}"

    def batch(self, rng: random.Random, weights: dict[int, float], batch_size: int, seq_len: int,
              device) -> tuple[torch.Tensor, torch.Tensor]:
        stages = [s for s in weights if self.by_stage.get(s)]
        w = [weights[s] for s in stages]
        xs, ys = [], []
        for _ in range(batch_size):
            buf: list[int] = []
            while len(buf) < seq_len + 1:                 # pack documents (each already BOS ... EOS)
                s = rng.choices(stages, w)[0]
                buf.extend(rng.choice(self.by_stage[s]))
            xs.append(buf[:seq_len]); ys.append(buf[1:seq_len + 1])
        x = torch.tensor(xs, dtype=torch.long, device=device)
        y = torch.tensor(ys, dtype=torch.long, device=device)
        return x, y
