"""From-scratch tokenizer for mathematical text (no pretrained vocabulary is used).

* Pre-tokenisation keeps every digit as its own piece, so numbers are never merged
  (digit-level arithmetic is far easier for a small model).
* Words/symbols are merged by byte-pair encoding learned on the training corpus only.
* Base alphabet = printable ASCII + newline + any other character seen in training.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from typing import Iterable

PAD, BOS, EOS, UNK = "<pad>", "<bos>", "<eos>", "<unk>"
SPECIALS = [PAD, BOS, EOS, UNK]
_PRE = re.compile(r" ?[A-Za-z_]+|\d| ?[^\sA-Za-z_\d]|\s")


def pretokenize(text: str) -> list[str]:
    return _PRE.findall(text)


class MathTokenizer:
    def __init__(self, vocab: list[str], merges: list[tuple[str, str]]):
        self.vocab = vocab
        self.token_to_id = {t: i for i, t in enumerate(vocab)}
        self.merges = merges
        self.ranks = {tuple(m): i for i, m in enumerate(merges)}
        self._cache: dict[str, list[str]] = {}
        self.pad_id, self.bos_id, self.eos_id, self.unk_id = (self.token_to_id[s] for s in SPECIALS)

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    # ---------------- training ----------------
    @classmethod
    def train(cls, texts: Iterable[str], vocab_size: int = 1024) -> "MathTokenizer":
        word_freq: Counter[str] = Counter()
        alphabet = set(chr(c) for c in range(32, 127)) | {"\n"}
        for t in texts:
            alphabet.update(t)
            word_freq.update(pretokenize(t))
        vocab = list(SPECIALS) + sorted(alphabet)
        words = {w: list(w) for w in word_freq if len(w) > 1 and not w.strip().isdigit()}
        merges: list[tuple[str, str]] = []
        while len(vocab) < vocab_size:
            pairs: Counter[tuple[str, str]] = Counter()
            for w, syms in words.items():
                f = word_freq[w]
                for a, b in zip(syms, syms[1:]):
                    pairs[(a, b)] += f
            if not pairs:
                break
            (a, b), cnt = pairs.most_common(1)[0]
            if cnt < 2:
                break
            merges.append((a, b)); vocab.append(a + b)
            for w, syms in words.items():
                i, out = 0, []
                while i < len(syms):
                    if i < len(syms) - 1 and syms[i] == a and syms[i + 1] == b:
                        out.append(a + b); i += 2
                    else:
                        out.append(syms[i]); i += 1
                words[w] = out
        return cls(vocab, merges)

    # ---------------- encode / decode ----------------
    def _bpe(self, piece: str) -> list[str]:
        if piece in self._cache:
            return self._cache[piece]
        syms = list(piece)
        while len(syms) > 1:
            cands = [(self.ranks[(a, b)], i) for i, (a, b) in enumerate(zip(syms, syms[1:])) if (a, b) in self.ranks]
            if not cands:
                break
            _, i = min(cands)
            syms[i:i + 2] = [syms[i] + syms[i + 1]]
        self._cache[piece] = syms
        return syms

    def encode(self, text: str, bos: bool = False, eos: bool = False) -> list[int]:
        ids = [self.bos_id] if bos else []
        for piece in pretokenize(text):
            for s in self._bpe(piece):
                ids.append(self.token_to_id.get(s, self.unk_id))
        if eos:
            ids.append(self.eos_id)
        return ids

    def decode(self, ids: Iterable[int]) -> str:
        out = []
        for i in ids:
            t = self.vocab[i]
            if t in SPECIALS:
                continue
            out.append(t)
        return "".join(out)

    # ---------------- persistence ----------------
    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"vocab": self.vocab, "merges": self.merges}, f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "MathTokenizer":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return cls(d["vocab"], [tuple(m) for m in d["merges"]])
