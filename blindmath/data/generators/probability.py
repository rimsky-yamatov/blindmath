"""Stage 5: counting and probability (exact fractions)."""
from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction
from functools import lru_cache
from typing import Iterator

from .common import rec, qa

DOMAIN, STAGE = "probability", 5


@lru_cache(None)
def stirling2(n, k):
    if n == k: return 1
    if k == 0 or k > n: return 0
    return k * stirling2(n - 1, k) + stirling2(n - 1, k - 1)


@lru_cache(None)
def partitions(n, m=None):
    m = n if m is None else m
    if n == 0: return 1
    if n < 0 or m == 0: return 0
    return partitions(n - m, m) + partitions(n, m - 1)


def derangements(n):
    d = [1, 0]
    for i in range(2, n + 1): d.append((i - 1) * (d[-1] + d[-2]))
    return d[n]


def gen_dice(rng):
    k, s = rng.randint(1, 3), None
    s = rng.randint(k, 6 * k)
    cnt = sum(1 for t in itertools.product(range(1, 7), repeat=k) if sum(t) == s)
    return qa(f"Probability that {k} fair dice sum to {s}?", f"{cnt} favourable of {6 ** k}", str(Fraction(cnt, 6 ** k)))


def gen_binomial(rng):
    n = rng.randint(2, 12); k = rng.randint(0, n); p = Fraction(1, rng.randint(2, 6))
    pr = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
    return qa(f"{n} independent trials, success probability {p}. P(exactly {k} successes)?", "C(n,k) p^k (1-p)^(n-k)", str(pr))


def gen_expectation(rng):
    vals = rng.sample(range(-5, 15), 4); w = [rng.randint(1, 6) for _ in range(4)]; t = sum(w)
    e = sum(Fraction(v * wi, t) for v, wi in zip(vals, w))
    return qa(f"X takes values {vals} with probabilities {[str(Fraction(wi, t)) for wi in w]}. E[X]?", "sum v*p", str(e))


def gen_conditional(rng):
    a, b, c, d = (rng.randint(1, 20) for _ in range(4))
    return qa(f"Counts: A&B={a}, A&notB={b}, notA&B={c}, notA&notB={d}. P(A | B)?", f"{a}/({a}+{c})", str(Fraction(a, a + c)))


def gen_special_counts(rng):
    n = rng.randint(1, 12)
    kind = rng.choice(["catalan", "stirling2", "derangements", "partitions", "bell_like"])
    if kind == "catalan": return qa(f"Catalan number C_{n}?", "C(2n,n)/(n+1)", str(math.comb(2 * n, n) // (n + 1)))
    if kind == "stirling2":
        k = rng.randint(1, n); return qa(f"Stirling number of the second kind S({n},{k})?", "S(n,k)=k S(n-1,k)+S(n-1,k-1)", str(stirling2(n, k)))
    if kind == "derangements": return qa(f"Number of derangements of {n} items?", "D(n)=(n-1)(D(n-1)+D(n-2))", str(derangements(n)))
    if kind == "partitions": return qa(f"Number of integer partitions of {n}?", "p(n,m) recursion", str(partitions(n)))
    return qa(f"Bell number B_{n}?", "sum_k S(n,k)", str(sum(stirling2(n, k) for k in range(n + 1))))


def gen_birthday(rng):
    d, k = rng.randint(5, 40), rng.randint(2, 6)
    p = Fraction(1)
    for i in range(k): p *= Fraction(d - i, d)
    return qa(f"{k} people, {d} equally likely days. P(all different)?", "product (d-i)/d", str(p))


GENS = [gen_dice, gen_binomial, gen_expectation, gen_conditional, gen_special_counts, gen_birthday]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
