"""Machine-check every Lean training template (so the corpus contains only proofs Lean accepts)."""
from __future__ import annotations

import argparse
import random

from blindmath.data.generators.lean_proofs import iter_items
from blindmath.theorem.lean_runner import LeanRunner


def verify(n: int = 200, seed: int = 0, chunk: int = 50) -> tuple[int, list[str]]:
    runner = LeanRunner(timeout=300)
    items = list(iter_items(random.Random(seed), n))
    failures: list[str] = []
    for i in range(0, len(items), chunk):
        part = items[i:i + chunk]
        res = runner.check_source("\n\n".join(it.source() for it in part))
        if not res.accepted:
            # locate the failing items one by one
            for it in part:
                r1 = runner.check_source(it.source())
                if not r1.accepted:
                    failures.append(f"{it.family}: {it.header}  -> {r1.error_text(200)}")
    return len(items), failures


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    total, bad = verify(a.n, a.seed)
    print(f"checked {total} templates, {len(bad)} failures")
    for b in bad:
        print("FAIL", b)
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
