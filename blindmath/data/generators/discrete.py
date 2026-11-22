"""Stage 5: discrete mathematics (counting, recurrences, graphs, binary)."""
from __future__ import annotations

import itertools
import math
import random
from typing import Iterator

from .common import rec, qa

DOMAIN, STAGE = "discrete", 5


def gen_comb(rng):
    n = rng.randint(2, 20); k = rng.randint(0, n)
    kind = rng.choice(["C", "P"])
    return qa(f"{'C' if kind == 'C' else 'P'}({n},{k}) = ?", "n!/(k!(n-k)!)" if kind == "C" else "n!/(n-k)!",
              str(math.comb(n, k) if kind == "C" else math.perm(n, k)))


def gen_incl_excl(rng):
    N = rng.randint(30, 300); a, b = rng.sample([2, 3, 5, 7], 2)
    cnt = N // a + N // b - N // (a * b)
    return qa(f"How many integers in 1..{N} are divisible by {a} or {b}?",
              f"{N // a} + {N // b} - {N // (a * b)} (inclusion-exclusion)", str(cnt))


def gen_recurrence(rng):
    a, b = rng.randint(1, 3), rng.randint(0, 3)
    x0, n = rng.randint(0, 4), rng.randint(3, 9)
    seq = [x0]
    for _ in range(n): seq.append(a * seq[-1] + b)
    return qa(f"x_0={x0}, x_(k+1) = {a}*x_k + {b}. Compute x_{n}.", ", ".join(map(str, seq)), str(seq[-1]))


def gen_graph(rng):
    n = rng.randint(4, 7)
    edges = [e for e in itertools.combinations(range(1, n + 1), 2) if rng.random() < 0.5]
    deg = [sum(1 for e in edges if v in e) for v in range(1, n + 1)]
    # connected components by union-find
    parent = list(range(n + 1))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in edges: parent[find(a)] = find(b)
    comps = len({find(v) for v in range(1, n + 1)})
    kind = rng.choice(["degrees", "components", "handshake"])
    g = f"Graph on 1..{n}, edges {edges}."
    if kind == "degrees": return qa(g + " Degree sequence?", "count incident edges", str(deg))
    if kind == "components": return qa(g + " Number of connected components?", "union-find", str(comps))
    return qa(g + " Sum of degrees?", f"2*|E| = 2*{len(edges)}", str(sum(deg)))


def gen_binary(rng):
    n = rng.randint(0, 5000)
    kind = rng.choice(["to_bin", "popcount", "bitlen"])
    if kind == "to_bin": return qa(f"{n} in binary?", "repeated division by 2", bin(n)[2:])
    if kind == "popcount": return qa(f"Number of 1 bits in binary of {n}?", bin(n)[2:], str(bin(n).count("1")))
    return qa(f"Number of bits needed for {n}?", "", str(max(n.bit_length(), 1)))


def gen_pigeonhole(rng):
    m, n = rng.randint(2, 12), rng.randint(13, 100)
    return qa(f"Place {n} objects into {m} boxes. Minimum size of the fullest box?", "pigeonhole: ceil(n/m)", str(-(-n // m)))


def gen_fib_identity(rng):
    n = rng.randint(1, 15)
    F = [0, 1]
    for _ in range(n + 2): F.append(F[-1] + F[-2])
    return qa(f"Check sum F_1..F_{n} = F_({n + 2}) - 1 for Fibonacci (F_1=F_2=1).",
              f"sum={sum(F[1:n + 1])}, F_{n + 2}-1={F[n + 2] - 1}", "holds")


GENS = [gen_comb, gen_incl_excl, gen_recurrence, gen_graph, gen_binary, gen_pigeonhole, gen_fib_identity]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
