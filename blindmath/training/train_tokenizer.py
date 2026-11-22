"""Train the tokenizer on the training split only (never on experiment files)."""
from __future__ import annotations

import argparse
import os

from blindmath.data.schema import read_jsonl
from blindmath.tokenizer import MathTokenizer


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--vocab-size", type=int, default=1024)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    texts = (r.text for r in read_jsonl(os.path.join(a.corpus, "train.jsonl")))
    tok = MathTokenizer.train(texts, a.vocab_size)
    out = a.out or os.path.join(a.corpus, "tokenizer.json")
    tok.save(out)
    print(f"saved {out} (vocab={tok.vocab_size})")


if __name__ == "__main__":
    main()
