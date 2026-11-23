import os

from blindmath.data import shards
from blindmath.data.generators.common import rec


def test_write_and_read_shards(tmp_path):
    recs = [rec("arithmetic", "g", f"Q: {i} + 1 = ?\nA: {i + 1}\n", 1) for i in range(500)]
    names = shards.write_shards(str(tmp_path), recs, shard_mb=0.005)
    assert len(names) > 3 and names[0] == "train-00000.jsonl"
    got = [r.text for r in shards.iter_train(str(tmp_path))]
    assert got == [r.text for r in recs]                       # order and content preserved
    assert all(os.path.getsize(tmp_path / n) < 0.02 * 1024 * 1024 for n in names)
