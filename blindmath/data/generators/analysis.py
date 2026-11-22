"""Stage 6: analysis (sequences, limits, series, derivatives, integrals; exact rational arithmetic)."""
from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Iterator

from .common import rec, qa

DOMAIN, STAGE = "analysis", 6


def gen_derivative(rng):
    c = [rng.randint(-6, 6) for _ in range(rng.randint(2, 5))]
    if c[-1] == 0: c[-1] = 1
    d = [i * c[i] for i in range(1, len(c))]
    f = lambda c: " + ".join(f"{a}x^{i}" for i, a in enumerate(c) if a) or "0"
    return qa(f"d/dx of {f(c)}?", "power rule term by term", f(d))


def gen_integral(rng):
    c = [rng.randint(-5, 5) for _ in range(rng.randint(1, 3))]
    a, b = rng.randint(0, 3), rng.randint(4, 7)
    F = lambda x: sum(Fraction(ci, i + 1) * x ** (i + 1) for i, ci in enumerate(c))
    f = " + ".join(f"{ci}x^{i}" for i, ci in enumerate(c))
    return qa(f"Integral of {f} from {a} to {b}?", "antiderivative F(b)-F(a)", str(F(b) - F(a)))


def gen_geometric(rng):
    r = Fraction(1, rng.randint(2, 6)); a = rng.randint(1, 9); n = rng.randint(3, 8)
    s = sum(a * r ** i for i in range(n))
    return qa(f"Sum of a*r^i for i=0..{n - 1} with a={a}, r={r}?", f"a(1-r^n)/(1-r); infinite sum would be {a / (1 - r)}" if False else "a(1-r^n)/(1-r)", str(s))


def gen_epsilon_N(rng):
    k = rng.randint(1, 5); eps = Fraction(1, rng.choice([10, 100, 1000]))
    N = math.floor(k / eps) + 1
    return qa(f"For the sequence a_n = {k}/n -> 0, find a natural N with |a_n| < {eps} for all n >= N.",
              f"{k}/n < {eps} <=> n > {k / eps}", f"N = {N}")


def gen_limit_ratio(rng):
    a, b, c, d = (rng.randint(1, 9) for _ in range(4))
    return qa(f"lim n->inf ({a}n + {b}) / ({c}n + {d}) = ?", "divide numerator and denominator by n", str(Fraction(a, c)))


def gen_floor_ceil(rng):
    x = Fraction(rng.randint(-100, 100), rng.randint(1, 9))
    return qa(f"floor({x}) and ceil({x})?", "", f"{math.floor(x)}, {math.ceil(x)}")


def gen_inequality(rng):
    a, b = rng.randint(1, 30), rng.randint(1, 30)
    am, gm2 = Fraction(a + b, 2), a * b
    return qa(f"AM-GM check for a={a}, b={b}: compare ((a+b)/2)^2 and a*b.", f"{am ** 2} vs {gm2}",
              f"{am ** 2} >= {gm2}" )


GENS = [gen_derivative, gen_integral, gen_geometric, gen_epsilon_N, gen_limit_ratio, gen_floor_ceil, gen_inequality]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
