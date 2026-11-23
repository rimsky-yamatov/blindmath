"""Phase 6: study unknown maps and discover lemmas. Everything is logged with its proper kind.

Pipeline per map: (1) computation: explore orbits  (2) hypothesis: finite-data conjectures
(3) computation: counterexample search for each conjecture  (4) conjectures that survive are kept as
*hypotheses* (never as theorems). Formal results come only from Lean (see phase7 / proof search).
"""
from __future__ import annotations

import argparse
import json
import os

from blindmath.experiments.ledger import Ledger
from blindmath.experiments.targets import UNKNOWN_MAPS
from blindmath.reasoning.explorer import explore, find_counterexample, orbit_info
from blindmath.theorem.library import TheoremLibrary


def conjectures(fn):
    """Generic template conjectures about a map; each returns (text, predicate on n)."""
    yield "every orbit eventually enters a cycle", lambda n: orbit_info(fn, n, 2000).found_cycle
    yield "g(n) <= n for all n >= 1", lambda n: fn(n) <= n
    yield "g(n) < n for all n >= 1", lambda n: fn(n) < n
    yield "g(n) >= 1 for all n >= 1", lambda n: fn(n) >= 1
    yield "the orbit of every n has peak at most 10*n", lambda n: orbit_info(fn, n, 2000).peak <= 10 * n


def run(out_dir: str, upper: int = 3000) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    led = Ledger(os.path.join(out_dir, "ledger.jsonl"))
    lib = TheoremLibrary(os.path.join(out_dir, "theorems"))
    summary = {}
    for key, (desc, fn) in UNKNOWN_MAPS.items():
        ex = explore(fn, 1, upper, 2000)
        led.log("computation", map=key, description=desc, **ex.summary())
        for text, pred in conjectures(fn):
            led.log("hypothesis", map=key, text=text, status="proposed")
            ce = find_counterexample(pred, range(1, upper + 1))
            led.log("computation", map=key, text=f"counterexample search for: {text}",
                    range=[1, upper], counterexample=ce, note="finite search; absence of a counterexample proves nothing")
            lib.add_conjecture(f"[{key}: {desc}] {text}", "refuted" if ce is not None else "numerically_supported",
                               f"counterexample {ce}" if ce is not None else f"no counterexample for 1..{upper}")
            summary.setdefault(key, []).append({"conjecture": text, "counterexample": ce})
    lib.render_markdown()
    with open(os.path.join(out_dir, "phase6_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/phase6")
    ap.add_argument("--upper", type=int, default=3000)
    a = ap.parse_args(argv)
    print(json.dumps(run(a.out, a.upper), indent=1, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
