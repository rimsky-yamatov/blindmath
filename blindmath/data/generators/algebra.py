"""Stage 4: algebra (polynomials, linear equations, small groups/rings, 2x2 matrices)."""
from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Iterator

from .common import rec, qa

DOMAIN, STAGE = "algebra", 4


def _poly_str(c):
    terms = []
    for i in range(len(c) - 1, -1, -1):
        if c[i] == 0: continue
        t = f"{abs(c[i])}" if i == 0 else (f"{abs(c[i]) if abs(c[i]) != 1 else ''}x" + (f"^{i}" if i > 1 else ""))
        terms.append(("-" if c[i] < 0 else "+") + t)
    s = "".join(terms) or "0"
    return s[1:] if s.startswith("+") else s


def gen_linear(rng):
    a, x, b = rng.choice([i for i in range(-9, 10) if i]), rng.randint(-20, 20), rng.randint(-30, 30)
    c = a * x + b
    return qa(f"Solve {a}x + {b} = {c}.", f"{a}x = {c - b}", f"x = {x}")


def gen_expand(rng):
    a, b = rng.randint(1, 9), rng.randint(-9, 9)
    n = rng.randint(2, 3)
    coeffs = [math.comb(n, k) * a ** k * b ** (n - k) for k in range(n + 1)]
    return qa(f"Expand ({a}x + {b})^{n}.", f"binomial theorem n={n}", _poly_str(coeffs))


def gen_quadratic(rng):
    r1, r2 = rng.randint(-9, 9), rng.randint(-9, 9)
    b, c = -(r1 + r2), r1 * r2
    return qa(f"Factor x^2 + {b}x + {c}." if b >= 0 else f"Factor x^2 - {-b}x + {c}." if c >= 0 else f"Factor x^2 - {-b}x - {-c}.",
              f"sum of roots={r1 + r2}, product={r1 * r2}", f"(x - {r1})(x - {r2})")


def gen_poly_eval(rng):
    c = [rng.randint(-5, 5) for _ in range(rng.randint(2, 4))]
    if c[-1] == 0: c[-1] = 1
    x = rng.randint(-4, 4)
    val = sum(ci * x ** i for i, ci in enumerate(c))
    return qa(f"p(x) = {_poly_str(c)}. Compute p({x}).", "Horner scheme", str(val))


def gen_poly_division(rng):
    r = rng.randint(-5, 5); c = [rng.randint(-5, 5) for _ in range(3)]
    if c[-1] == 0: c[-1] = 2
    val = sum(ci * r ** i for i, ci in enumerate(c))
    return qa(f"Remainder of {_poly_str(c)} divided by (x - {r})?", "remainder theorem: p(r)", str(val))


def gen_det(rng):
    a, b, c, d = (rng.randint(-6, 6) for _ in range(4))
    det = a * d - b * c
    return qa(f"det [[{a},{b}],[{c},{d}]] = ?", f"{a}*{d} - {b}*{c}", str(det))


def gen_group_zn(rng):
    n = rng.randint(2, 24); a = rng.randint(0, n - 1)
    order = n // math.gcd(a, n) if a else 1
    return qa(f"In the additive group Z_{n}, what is the order of {a}?", f"n/gcd(a,n) = {n}/{math.gcd(a, n)}", str(order))


def gen_perm(rng):
    n = rng.randint(3, 6); p = list(range(1, n + 1)); rng.shuffle(p)
    seen, cycles = set(), []
    for i in range(1, n + 1):
        if i in seen: continue
        c, j = [], i
        while j not in seen: seen.add(j); c.append(j); j = p[j - 1]
        cycles.append(tuple(c))
    order = 1
    for c in cycles: order = order * len(c) // math.gcd(order, len(c))
    return qa(f"Permutation of 1..{n} given as images {p}. Cycle decomposition and order?",
              "follow i -> p(i)", f"{''.join(str(c) for c in cycles)}, order {order}")


def gen_fraction(rng):
    a, b = Fraction(rng.randint(1, 9), rng.randint(1, 9)), Fraction(rng.randint(1, 9), rng.randint(1, 9))
    op = rng.choice(["+", "*"])
    r = a + b if op == "+" else a * b
    return qa(f"{a} {op} {b} = ?", "common denominator" if op == "+" else "multiply numerators and denominators", str(r))


GENS = [gen_linear, gen_expand, gen_quadratic, gen_poly_eval, gen_poly_division, gen_det,
        gen_group_zn, gen_perm, gen_fraction]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
