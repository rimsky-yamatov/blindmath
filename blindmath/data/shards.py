"""Sharded corpus files: train-00000.jsonl, train-00001.jsonl, ... (each below GitHub's 100MB limit)."""
from __future__ import annotations

import glob
import os
from typing import Iterator

from blindmath.data.schema import Record, read_jsonl

SHARD_MB = 22


def train_files(corpus: str) -> list[str]:
    """Training shards of a corpus directory (falls back to a single train.jsonl)."""
    shards = sorted(glob.glob(os.path.join(corpus, "train-*.jsonl")))
    if shards:
        return shards
    single = os.path.join(corpus, "train.jsonl")
    return [single] if os.path.exists(single) else []


def iter_train(corpus: str) -> Iterator[Record]:
    for f in train_files(corpus):
        yield from read_jsonl(f)


def write_shards(corpus: str, records, shard_mb: int = SHARD_MB) -> list[str]:
    """Write records into size-capped shards; returns the shard file names."""
    limit, names, idx, size, fh = shard_mb * 1024 * 1024, [], 0, 0, None
    try:
        for r in records:
            if fh is None or size >= limit:
                if fh:
                    fh.close()
                name = f"train-{idx:05d}.jsonl"
                names.append(name); idx += 1; size = 0
                fh = open(os.path.join(corpus, name), "w", encoding="utf-8")
            line = r.to_json() + "\n"
            fh.write(line); size += len(line.encode("utf-8"))
    finally:
        if fh:
            fh.close()
    return names
