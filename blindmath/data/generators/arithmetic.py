"""Stage 1: arithmetic, integers, sets (algorithmic, verifiable)."""
from __future__ import annotations

import random
from typing import Iterator

from .common import rec, qa

DOMAIN, STAGE = "arithmetic", 1


def _add_steps(a: int, b: int) -> str:
    da, db = str(a)[::-1], str(b)[::-1]
    carry, out, parts = 0, [], []
    for i in range(max(len(da), len(db))):
        x = int(da[i]) if i < len(da) else 0
        y = int(db[i]) if i < len(db) else 0
        s = x + y + carry
        parts.append(f"{x}+{y}+{carry}={s}")
        out.append(str(s % 10)); carry = s // 10
    if carry:
        out.append(str(carry))
    return "; ".join(parts) + f" => {''.join(reversed(out))}"


def gen_add(rng: random.Random) -> str:
    a, b = rng.randint(0, 10 ** rng.randint(1, 6)), rng.randint(0, 10 ** rng.randint(1, 6))
    return qa(f"{a} + {b} = ?", _add_steps(a, b), str(a + b))


def gen_sub(rng):
    a, b = rng.randint(0, 10 ** rng.randint(1, 6)), rng.randint(0, 10 ** rng.randint(1, 6))
    return qa(f"{a} - {b} = ?", "", str(a - b))


def gen_mul(rng):
    a, b = rng.randint(0, 10 ** rng.randint(1, 4)), rng.randint(0, 10 ** rng.randint(1, 3))
    parts = [f"{a}*{d}*10^{i}={a * int(d) * 10 ** i}" for i, d in enumerate(reversed(str(b)))]
    return qa(f"{a} * {b} = ?", "; ".join(parts) + " => sum", str(a * b))


def gen_divmod(rng):
    b = rng.randint(2, 10 ** rng.randint(1, 3))
    a = rng.randint(0, 10 ** rng.randint(1, 5))
    q, r = divmod(a, b)
    return qa(f"Divide {a} by {b}: quotient and remainder?", f"{a} = {b}*{q} + {r}, 0 <= {r} < {b}",
              f"q={q}, r={r}")


def gen_compare(rng):
    a, b = rng.randint(-1000, 1000), rng.randint(-1000, 1000)
    sym = "<" if a < b else (">" if a > b else "=")
    return qa(f"Compare {a} and {b}.", "", f"{a} {sym} {b}")


def gen_power(rng):
    a, e = rng.randint(2, 12), rng.randint(0, 9)
    return qa(f"{a}^{e} = ?", " * ".join([str(a)] * max(e, 1)) if e else "a^0 = 1", str(a ** e))


def gen_order_of_ops(rng):
    a, b, c, d = (rng.randint(1, 20) for _ in range(4))
    e = f"{a} + {b} * ({c} - {d})"
    return qa(f"Evaluate {e}.", f"{c}-{d}={c - d}; {b}*{c - d}={b * (c - d)}; {a}+{b * (c - d)}",
              str(a + b * (c - d)))


def gen_sets(rng):
    A = sorted(rng.sample(range(1, 15), rng.randint(2, 6)))
    B = sorted(rng.sample(range(1, 15), rng.randint(2, 6)))
    op = rng.choice(["union", "intersection", "difference", "symmetric difference"])
    s, t = set(A), set(B)
    r = {"union": s | t, "intersection": s & t, "difference": s - t,
         "symmetric difference": s ^ t}[op]
    return qa(f"A={set(A)}, B={set(B)}. Compute the {op} of A and B.",
              f"|A|={len(A)}, |B|={len(B)}", "{" + ", ".join(map(str, sorted(r))) + "}")


def gen_parity_digits(rng):
    n = rng.randint(1, 10 ** rng.randint(1, 6))
    kind = rng.choice(["digit sum", "number of digits", "parity", "last digit of square"])
    if kind == "digit sum":
        ans = str(sum(map(int, str(n))))
    elif kind == "number of digits":
        ans = str(len(str(n)))
    elif kind == "parity":
        ans = "even" if n % 2 == 0 else "odd"
    else:
        ans = str(n * n % 10)
    return qa(f"{kind} of {n}?", "", ans)


GENS = [gen_add, gen_sub, gen_mul, gen_divmod, gen_compare, gen_power, gen_order_of_ops,
        gen_sets, gen_parity_digits]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
