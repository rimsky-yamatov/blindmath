"""Generic exploration of iterated integer maps (supports Phase 6: studying *unknown* maps).

These exercises teach the model how to explore a map: compute orbits, detect fixed points and
cycles, count steps until repetition. The maps used here are generic (digit maps, modular maps,
squaring maps). The corpus audit removes any generated item that matches the target's fingerprint.
"""
from __future__ import annotations

import random
from typing import Callable, Iterator

from .common import rec, qa

DOMAIN, STAGE = "dynamics", 6


def _digit_sum(n): return sum(map(int, str(n)))
def _sq_digits(n): return sum(int(d) ** 2 for d in str(n))
def _rev_add(n): return n + int(str(n)[::-1])
def _largest_sq_gap(n):
    r = int(n ** 0.5)
    while r * r > n: r -= 1
    while (r + 1) ** 2 <= n: r += 1
    return n - r * r
def _floor_half(n): return n // 2


def _random_modmap(rng):
    m = rng.randint(5, 40); a = rng.randint(1, m - 1); b = rng.randint(0, m - 1)
    return f"g(n) = ({a}*n + {b}) mod {m}", (lambda n, a=a, b=b, m=m: (a * n + b) % m)


def _random_sqmap(rng):
    m = rng.randint(7, 60); c = rng.randint(0, m - 1)
    return f"g(n) = (n*n + {c}) mod {m}", (lambda n, c=c, m=m: (n * n + c) % m)


FIXED_MAPS = [
    ("g(n) = digit sum of n", _digit_sum),
    ("g(n) = sum of squares of the digits of n", _sq_digits),
    ("g(n) = n + reverse(n)", _rev_add),
    ("g(n) = n - (largest square <= n)", _largest_sq_gap),
    ("g(n) = floor(n/2)", _floor_half),
]


def _orbit(f: Callable[[int], int], n: int, limit: int = 60):
    seen, seq = {}, []
    while n not in seen and len(seq) < limit:
        seen[n] = len(seq); seq.append(n); n = f(n)
    return seq, (seen.get(n) if n in seen else None), n


def gen_orbit(rng):
    desc, f = rng.choice(FIXED_MAPS + [_random_modmap(rng), _random_sqmap(rng)]) if rng.random() < 0.5 \
        else rng.choice(FIXED_MAPS)
    n0 = rng.randint(1, 500)
    k = rng.randint(3, 8)
    seq, x = [n0], n0
    for _ in range(k): x = f(x); seq.append(x)
    return qa(f"Map {desc}. Compute the first {k} iterates starting at {n0}.", "apply g repeatedly",
              " -> ".join(map(str, seq)))


def gen_cycle(rng):
    desc, f = rng.choice([_random_modmap(rng), _random_sqmap(rng)])
    n0 = rng.randint(0, 40)
    seq, start, rep = _orbit(f, n0)
    if start is None:
        return gen_cycle(rng)
    cyc = seq[start:]
    return qa(f"Map {desc}. Orbit of {n0}: tail length and cycle length?", " -> ".join(map(str, seq)) + f" -> {rep}",
              f"tail={start}, cycle={len(cyc)}, cycle elements {cyc}")


def gen_fixed_points(rng):
    desc, f = _random_modmap(rng) if rng.random() < .5 else _random_sqmap(rng)
    m = int(desc.split("mod ")[1].rstrip(")"))
    fps = [x for x in range(m) if f(x) == x]
    return qa(f"Map {desc} on {{0..{m - 1}}}. List the fixed points (g(n)=n).", "check n = 0..m-1", str(fps))


def gen_monotone_invariant(rng):
    desc, f = rng.choice(FIXED_MAPS[:2])
    n = rng.randint(10, 9999)
    return qa(f"Map {desc}. Is g(n) < n for n={n}? Give g(n).", "", f"g({n}) = {f(n)}, {'yes' if f(n) < n else 'no'}")


GENS = [gen_orbit, gen_cycle, gen_fixed_points, gen_monotone_invariant]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
