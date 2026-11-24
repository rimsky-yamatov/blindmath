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


def gen_base_convert(rng):
    n, b = rng.randint(0, 5000), rng.choice([2, 3, 5, 7, 8, 16])
    digs, m = "", n
    while m: digs = "0123456789abcdef"[m % b] + digs; m //= b
    return qa(f"Write {n} in base {b}.", "repeated division by the base", digs or "0")


def gen_decimal_period(rng):
    q = rng.randint(2, 60); p = rng.randint(1, q - 1)
    seen, r, digs = {}, p, ""
    while r and r not in seen:
        seen[r] = len(digs); r *= 10; digs += str(r // q); r %= q
    if r == 0:
        return qa(f"Decimal expansion of {p}/{q}?", "long division", f"0.{digs} (terminates)")
    i = seen[r]
    return qa(f"Decimal expansion of {p}/{q}?", "long division until a remainder repeats", f"0.{digs[:i]}({digs[i:]}) repeating")


def gen_lcm_word(rng):
    a, b = rng.randint(2, 60), rng.randint(2, 60)
    import math
    return qa(f"Two events repeat every {a} and {b} days. After how many days do they coincide again?", f"lcm({a},{b}) = {a * b}/gcd", str(a * b // math.gcd(a, b)))


def gen_percent(rng):
    p, n = rng.choice([5, 10, 12, 15, 20, 25, 40, 75]), rng.randint(2, 400) * 4
    return qa(f"What is {p}% of {n}?", f"{n}*{p}/100", str(n * p / 100).rstrip("0").rstrip("."))


def gen_isqrt(rng):
    import math
    n = rng.randint(1, 10 ** rng.randint(2, 8))
    r = math.isqrt(n)
    return qa(f"Integer square root (floor) of {n}?", f"{r}^2={r * r} <= {n} < {(r + 1) ** 2}", str(r))


def gen_bigmul(rng):
    a, b = rng.randint(10 ** 5, 10 ** 9), rng.randint(10 ** 3, 10 ** 6)
    return qa(f"{a} * {b} = ?", "split the second factor by digits and add", str(a * b))


GENS = [gen_add, gen_sub, gen_mul, gen_divmod, gen_compare, gen_power, gen_order_of_ops,
        gen_sets, gen_parity_digits, gen_base_convert, gen_decimal_period, gen_lcm_word, gen_percent, gen_isqrt,
        gen_bigmul]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        g = rng.choice(GENS)
        yield rec(DOMAIN, g.__name__, g(rng), STAGE)
