"""Build the training corpus: generate -> audit (drop leaks) -> dedupe -> split -> write JSONL + manifest.

Outputs (under --out):
  train-00000.jsonl ...     sharded training records with provenance fields (each shard < 25MB)
  val.jsonl                 validation records
  quarantine.jsonl          records dropped by the leak audit (rule 1)
  manifest.json             counts per domain/stage/source/license + audit summary (rule 2)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from collections import Counter

from blindmath.data import audit, shards
from blindmath.data.generators import (algebra, analysis, arithmetic, discrete, dynamics,
                                       logic, number_theory)
from blindmath.data.schema import write_jsonl

# domain -> (module, relative weight)
REGISTRY = {
    "arithmetic": (arithmetic, 1.0),
    "logic": (logic, 1.0),
    "number_theory": (number_theory, 1.5),
    "algebra": (algebra, 0.8),
    "discrete": (discrete, 0.8),
    "analysis": (analysis, 0.6),
    "dynamics": (dynamics, 0.8),
}


def _lean_domain():
    try:
        from blindmath.data.generators import lean_proofs
        return lean_proofs
    except ImportError:  # optional until Phase 5 generator exists
        return None


def build(out_dir: str, n_total: int, seed: int = 0, val_fraction: float = 0.02,
          include_lean: bool = True, with_repair: bool = False, repair_n: int = 1500) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(seed)
    reg = dict(REGISTRY)
    lean_mod = _lean_domain() if include_lean else None
    if lean_mod is not None:
        reg["lean_proofs"] = (lean_mod, 1.2)
    if with_repair:  # needs a Lean toolchain; uses real error messages
        from blindmath.data.generators import lean_repair
        reg["lean_repair"] = (lean_repair, 0.0)
    total_w = sum(w for k, (_, w) in reg.items() if k != "lean_repair")

    def all_records():
        for name, (mod, w) in reg.items():
            n = repair_n if name == "lean_repair" else max(1, int(n_total * w / total_w))
            yield from mod.generate(random.Random(rng.randrange(1 << 30)), n)

    seen, kept = set(), []
    quarantine = os.path.join(out_dir, "quarantine.jsonl")
    for r in audit.filter_clean(all_records(), quarantine):
        h = hashlib.sha1(r.text.encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h); kept.append(r)
    rng.shuffle(kept)
    n_val = max(1, int(len(kept) * val_fraction))
    val, train = kept[:n_val], kept[n_val:]
    for stale in shards.train_files(out_dir):  # remove shards of an earlier build
        os.remove(stale)
    shard_names = shards.write_shards(out_dir, train)
    write_jsonl(os.path.join(out_dir, "val.jsonl"), val)

    # Independent re-audit of the *written* files (defence in depth).
    final = audit.audit_records(train + val)
    manifest = {
        "seed": seed, "requested": n_total, "train_shards": shard_names, "kept": len(kept), "train": len(train), "val": len(val),
        "by_domain": Counter(r.domain for r in kept), "by_stage": Counter(r.stage for r in kept),
        "by_kind": Counter(r.kind for r in kept), "by_source": Counter(r.source for r in kept),
        "by_license": Counter(r.license for r in kept),
        "quarantined": sum(1 for _ in open(quarantine, encoding="utf-8")),
        "final_audit": {"scanned": final.scanned, "flagged": final.flagged},
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, default=dict)
    assert final.flagged == 0, "leak audit failed on the final corpus"
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/corpus")
    ap.add_argument("--n", type=int, default=200_000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-lean", action="store_true")
    ap.add_argument("--repair-n", type=int, default=1500, help="number of Lean repair records (slow: calls Lean)")
    ap.add_argument("--with-repair", action="store_true", help="add Lean error-feedback repair data (needs Lean)")
    a = ap.parse_args(argv)
    m = build(a.out, a.n, a.seed, include_lean=not a.no_lean, with_repair=a.with_repair, repair_n=a.repair_n)
    print(json.dumps(m, ensure_ascii=False, indent=2, default=dict))


if __name__ == "__main__":
    main()
