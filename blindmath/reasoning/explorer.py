"""Computational exploration of integer maps (Phase 4/6/7). Results are *computations*, never proofs (rule 5).

Everything here is generic: it takes a function and probes it (orbits, cycles, growth, counterexamples).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable


@dataclass
class OrbitInfo:
    start: int
    tail: int                 # steps before entering a cycle (None if not found within budget)
    cycle: tuple[int, ...]    # the cycle entered
    peak: int                 # largest value seen
    steps_run: int
    found_cycle: bool


def orbit_info(fn: Callable[[int], int], n: int, max_steps: int = 10_000, cap: int = 10 ** 30) -> OrbitInfo:
    seen: dict[int, int] = {}
    seq: list[int] = []
    x, peak = n, n
    while len(seq) < max_steps:
        if x in seen:
            i = seen[x]
            return OrbitInfo(n, i, tuple(seq[i:]), peak, len(seq), True)
        seen[x] = len(seq); seq.append(x)
        if x > cap:
            break
        x = fn(x); peak = max(peak, x)
    return OrbitInfo(n, len(seq), (), peak, len(seq), False)


def canon_cycle(c: tuple[int, ...]) -> tuple[int, ...]:
    if not c:
        return c
    i = c.index(min(c))
    return c[i:] + c[:i]


@dataclass
class Exploration:
    lo: int
    hi: int
    cycles: dict[tuple[int, ...], int] = field(default_factory=dict)   # canonical cycle -> #starts
    unresolved: list[int] = field(default_factory=list)                # starts with no cycle within budget
    max_tail: int = 0
    max_tail_start: int = 0
    peak_ratio: float = 0.0
    peak_start: int = 0

    def summary(self) -> dict:
        return {"range": [self.lo, self.hi], "distinct_cycles": len(self.cycles),
                "cycles": {str(list(k)): v for k, v in self.cycles.items()},
                "unresolved_count": len(self.unresolved), "unresolved_head": self.unresolved[:10],
                "max_tail": self.max_tail, "max_tail_start": self.max_tail_start,
                "max_peak_over_start": round(self.peak_ratio, 3), "peak_ratio_start": self.peak_start,
                "note": "finite computation; not a proof"}


def explore(fn: Callable[[int], int], lo: int, hi: int, max_steps: int = 10_000) -> Exploration:
    ex = Exploration(lo, hi)
    for n in range(lo, hi + 1):
        info = orbit_info(fn, n, max_steps)
        if not info.found_cycle:
            ex.unresolved.append(n); continue
        key = canon_cycle(info.cycle)
        ex.cycles[key] = ex.cycles.get(key, 0) + 1
        if info.tail > ex.max_tail:
            ex.max_tail, ex.max_tail_start = info.tail, n
        if info.peak / n > ex.peak_ratio:
            ex.peak_ratio, ex.peak_start = info.peak / n, n
    return ex


def find_counterexample(pred: Callable[[int], bool], domain: Iterable[int]) -> int | None:
    """Return the first n in `domain` where pred(n) is False (None = none found; NOT a proof)."""
    for n in domain:
        if not pred(n):
            return n
    return None
