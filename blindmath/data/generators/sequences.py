"""Stage 6: sequences, series, continued fractions, periodicity."""
from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Iterator

from .common import rec, qa

DOMAIN, STAGE = "sequences", 6


def gen_arith_geo(rng):
    a, d, n = rng.randint(-9, 9), rng.randint(-5, 9), rng.randint(2, 30)
    if rng.random() < .5:
        return qa(f"Arithmetic sequence a_1={a}, difference {d}. a_{n} and S_{n}?", "a_n=a_1+(n-1)d, S=n(a_1+a_n)/2",
                  f"a_{n}={a + (n - 1) * d}, S_{n}={n * (2 * a + (n - 1) * d) // 2}")
    r = rng.randint(2, 4); n = rng.randint(2, 10); a = rng.randint(1, 5)
    return qa(f"Geometric sequence a_1={a}, ratio {r}. a_{n} and S_{n}?", "a_n=a_1 r^(n-1)", f"a_{n}={a * r ** (n - 1)}, S_{n}={a * (r ** n - 1) // (r - 1)}")


def gen_telescoping(rng):
    n = rng.randint(1, 40)
    s = sum(Fraction(1, k * (k + 1)) for k in range(1, n + 1))
    return qa(f"Sum of 1/(k(k+1)) for k=1..{n}?", "telescopes to 1 - 1/(n+1)", str(s))


def gen_cf(rng):
    p, q = rng.randint(1, 200), rng.randint(1, 200)
    a, b, cf = p, q, []
    while b: cf.append(a // b); a, b = b, a % b
    return qa(f"Continued fraction of {p}/{q}?", "Euclid quotients", str(cf))


def gen_pisano(rng):
    m = rng.randint(2, 30)
    a, b, k = 0, 1, 0
    while True:
        a, b = b, (a + b) % m; k += 1
        if (a, b) == (0, 1): break
    return qa(f"Period of Fibonacci numbers modulo {m}?", "first k with (F_k, F_(k+1)) = (0,1) mod m", str(k))


def gen_taylor(rng):
    n = rng.randint(1, 8)
    return qa(f"Coefficient of x^{n} in the Taylor series of e^(2x) at 0?", f"2^{n}/{n}!", str(Fraction(2 ** n, math.factorial(n))))


def gen_power_sum(rng):
    n, p = rng.randint(1, 25), rng.randint(1, 3)
    return qa(f"Sum of k^{p} for k=1..{n}?", "closed form / direct sum", str(sum(k ** p for k in range(1, n + 1))))


def gen_ratio_test(rng):
    a, b = rng.randint(1, 6), rng.randint(1, 6)
    kind = rng.choice(["geometric", "factorial"])
    if kind == "geometric":
        r = Fraction(a, b)
        return qa(f"Does sum of ({a}/{b})^k for k>=0 converge?", f"ratio {r}", "yes" if r < 1 else "no")
    return qa(f"Does sum of {a}^k / k! converge?", "ratio a/(k+1) -> 0", "yes")


GENS = [gen_arith_geo, gen_telescoping, gen_cf, gen_pisano, gen_taylor, gen_power_sum, gen_ratio_test]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
