"""Stage 4: linear algebra with exact rationals."""
from __future__ import annotations

import random
from fractions import Fraction
from typing import Iterator

from .common import rec, qa

DOMAIN, STAGE = "linear_algebra", 4


def _m(rng, n, r=6): return [[rng.randint(-r, r) for _ in range(n)] for _ in range(n)]


def det(m):
    if len(m) == 1: return m[0][0]
    return sum((-1) ** j * m[0][j] * det([row[:j] + row[j + 1:] for row in m[1:]]) for j in range(len(m)))


def _fmt(m): return "[" + ",".join("[" + ",".join(str(x) for x in r) + "]" for r in m) + "]"


def gen_det3(rng):
    m = _m(rng, 3, 5)
    return qa(f"det {_fmt(m)} = ?", "cofactor expansion along the first row", str(det(m)))


def gen_matmul(rng):
    a, b = _m(rng, 2), _m(rng, 2)
    c = [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    return qa(f"{_fmt(a)} * {_fmt(b)} = ?", "row times column", _fmt(c))


def gen_inverse(rng):
    a = _m(rng, 2)
    d = det(a)
    if d == 0: return gen_inverse(rng)
    inv = [[Fraction(a[1][1], d), Fraction(-a[0][1], d)], [Fraction(-a[1][0], d), Fraction(a[0][0], d)]]
    return qa(f"Inverse of {_fmt(a)}?", f"det={d}, adjugate / det", _fmt(inv))


def gen_system(rng):
    x, y = rng.randint(-9, 9), rng.randint(-9, 9)
    a, b, c, d = (rng.randint(-6, 6) for _ in range(4))
    if a * d - b * c == 0: return gen_system(rng)
    return qa(f"Solve {a}x + {b}y = {a * x + b * y}, {c}x + {d}y = {c * x + d * y}.", f"Cramer: det={a * d - b * c}", f"x={x}, y={y}")


def gen_dotcross(rng):
    u = [rng.randint(-6, 6) for _ in range(3)]; v = [rng.randint(-6, 6) for _ in range(3)]
    if rng.random() < .5:
        return qa(f"Dot product of {u} and {v}?", "sum of products", str(sum(p * q for p, q in zip(u, v))))
    cr = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    return qa(f"Cross product of {u} and {v}?", "determinant formula", str(cr))


def gen_eigen(rng):
    l1, l2 = rng.randint(-5, 5), rng.randint(-5, 5)
    tr, dt = l1 + l2, l1 * l2
    return qa(f"Eigenvalues of a 2x2 matrix with trace {tr} and determinant {dt}?", f"t^2 - {tr}t + {dt} = 0",
              str(sorted({l1, l2})))


def gen_matpow_mod(rng):
    m = rng.randint(2, 30); n = rng.randint(1, 20); a = _m(rng, 2, 4)
    r = [[1, 0], [0, 1]]
    for _ in range(n): r = [[sum(r[i][k] * a[k][j] for k in range(2)) % m for j in range(2)] for i in range(2)]
    return qa(f"{_fmt(a)}^{n} mod {m} = ?", "repeated multiplication mod m", _fmt(r))


GENS = [gen_det3, gen_matmul, gen_inverse, gen_system, gen_dotcross, gen_eigen, gen_matpow_mod]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
