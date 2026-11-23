"""Stage 4: coordinate geometry (exact integer/rational arithmetic)."""
from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Iterator

from .common import rec, qa

DOMAIN, STAGE = "geometry", 4


def _pt(rng, r=12): return rng.randint(-r, r), rng.randint(-r, r)


def gen_dist2(rng):
    (a, b), (c, d) = _pt(rng), _pt(rng)
    return qa(f"Squared distance between ({a},{b}) and ({c},{d})?", f"({c - a})^2 + ({d - b})^2", str((c - a) ** 2 + (d - b) ** 2))


def gen_midpoint(rng):
    (a, b), (c, d) = _pt(rng), _pt(rng)
    return qa(f"Midpoint of ({a},{b}) and ({c},{d})?", "average coordinates", f"({Fraction(a + c, 2)}, {Fraction(b + d, 2)})")


def gen_line(rng):
    (a, b), (c, d) = _pt(rng), _pt(rng)
    if a == c:
        return qa(f"Line through ({a},{b}) and ({c},{d})?", "same x", f"x = {a}")
    m = Fraction(d - b, c - a)
    return qa(f"Line through ({a},{b}) and ({c},{d}): slope and intercept?", f"slope=({d}-{b})/({c}-{a})",
              f"slope {m}, intercept {b - m * a}")


def gen_area(rng):
    p = [_pt(rng) for _ in range(3)]
    s = abs(p[0][0] * (p[1][1] - p[2][1]) + p[1][0] * (p[2][1] - p[0][1]) + p[2][0] * (p[0][1] - p[1][1]))
    return qa(f"Area of the triangle {p[0]}, {p[1]}, {p[2]}?", "shoelace: |sum|/2", str(Fraction(s, 2)))


def gen_pyth(rng):
    a, b = rng.randint(1, 40), rng.randint(1, 40)
    c2 = a * a + b * b; c = math.isqrt(c2)
    return qa(f"Is a right triangle with legs {a} and {b} having an integer hypotenuse?", f"{a}^2+{b}^2={c2}",
              f"yes, {c}" if c * c == c2 else "no")


def gen_circle(rng):
    r = rng.randint(1, 12); a, b = _pt(rng, 6)
    pts = [(x, y) for x in range(a - r, a + r + 1) for y in range(b - r, b + r + 1) if (x - a) ** 2 + (y - b) ** 2 == r * r]
    return qa(f"Number of integer points on the circle (x-{a})^2 + (y-{b})^2 = {r * r}?", "enumerate the square window", str(len(pts)))


def gen_polygon_angle(rng):
    n = rng.randint(3, 20)
    return qa(f"Sum of interior angles of a convex {n}-gon in degrees?", f"({n}-2)*180", str((n - 2) * 180))


def gen_triangle_ineq(rng):
    a, b, c = (rng.randint(1, 20) for _ in range(3))
    ok = a + b > c and a + c > b and b + c > a
    return qa(f"Can sides {a}, {b}, {c} form a (non-degenerate) triangle?", "check all three sums", "yes" if ok else "no")


GENS = [gen_dist2, gen_midpoint, gen_line, gen_area, gen_pyth, gen_circle, gen_polygon_angle, gen_triangle_ineq]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
