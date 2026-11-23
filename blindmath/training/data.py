"""Token streams from the corpus: tokenise once, sample documents by curriculum weight, pack to seq_len.

Prompt masking: the question / statement part of every document is context only. Loss is computed on the
reasoning and the answer/proof (everything from "\\nWork:" or "\\nA:" onwards), so capacity is spent on
solving, not on predicting random problem parameters.
"""
from __future__ import annotations

import random
from array import array
from collections import defaultdict

import torch

from blindmath.data.schema import read_jsonl
from blindmath.tokenizer import MathTokenizer

IGNORE = -100


def split_point(text: str) -> int:
    i = text.find("\nWork:")
    return i if i != -1 else max(text.rfind("\nA:"), 0)


class TokenizedCorpus:
    def __init__(self, paths: str | list[str], tok: MathTokenizer, max_len: int, mask_prompt: bool = True):
        paths = [paths] if isinstance(paths, str) else paths
        self.by_stage: dict[int, list[tuple[array, int]]] = defaultdict(list)
        code = "H" if tok.vocab_size < 65536 else "I"
        for path in paths:
            for r in read_jsonl(path):
                cut = split_point(r.text) if mask_prompt else 0
                head = tok.encode(r.text[:cut], bos=True) if cut else [tok.bos_id]
                tail = tok.encode(r.text[cut:], eos=True)
                ids = head + tail
                if len(ids) <= max_len + 1:
                    self.by_stage[r.stage].append((array(code, ids), len(head)))
        self.n_docs = sum(len(v) for v in self.by_stage.values())
        assert self.n_docs, f"no documents in {paths}"

    def batch(self, rng: random.Random, weights: dict[int, float], batch_size: int, seq_len: int,
              device) -> tuple[torch.Tensor, torch.Tensor]:
        stages = [s for s in weights if self.by_stage.get(s)]
        w = [weights[s] for s in stages]
        xs, ys = [], []
        for _ in range(batch_size):
            toks: list[int] = []
            labels: list[int] = []
            while len(toks) < seq_len + 1:                 # pack documents (each BOS ... EOS)
                s = rng.choices(stages, w)[0]
                ids, start = rng.choice(self.by_stage[s])
                toks.extend(ids)
                labels.extend([IGNORE] * start + list(ids[start:]))
            xs.append(toks[:seq_len]); ys.append(labels[1:seq_len + 1])
        x = torch.tensor(xs, dtype=torch.long, device=device)
        y = torch.tensor(ys, dtype=torch.long, device=device)
        return x, y
