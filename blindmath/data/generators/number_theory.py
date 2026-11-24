"""Stage 3 (elementary number theory, congruences) and stage 8 (advanced number theory)."""
from __future__ import annotations

import math
import random
from typing import Iterator

from .common import rec, qa

DOMAIN = "number_theory"


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def factorize(n: int) -> dict[int, int]:
    f, p = {}, 2
    while p * p <= n:
        while n % p == 0:
            f[p] = f.get(p, 0) + 1; n //= p
        p += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def _fmt_fact(f):
    return " * ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(f.items()))


def gen_gcd(rng):
    a, b = rng.randint(1, 5000), rng.randint(1, 5000)
    x, y, steps = a, b, []
    while y:
        steps.append(f"{x}={y}*{x // y}+{x % y}"); x, y = y, x % y
    return qa(f"gcd({a}, {b}) = ?", "; ".join(steps), str(x))


def gen_bezout(rng):
    a, b = rng.randint(2, 500), rng.randint(2, 500)
    def eg(a, b):
        if b == 0: return a, 1, 0
        g, x, y = eg(b, a % b); return g, y, x - (a // b) * y
    g, x, y = eg(a, b)
    return qa(f"Find integers x,y with {a}x + {b}y = gcd({a},{b}).", f"extended Euclid; gcd={g}",
              f"x={x}, y={y}  ({a}*{x} + {b}*{y} = {a * x + b * y})")


def gen_modop(rng):
    m = rng.randint(2, 60); a, b = rng.randint(0, 999), rng.randint(0, 999)
    op = rng.choice(["+", "-", "*"])
    v = {"+": a + b, "-": a - b, "*": a * b}[op] % m
    return qa(f"({a} {op} {b}) mod {m} = ?", f"{a}%{m}={a % m}, {b}%{m}={b % m}", str(v))


def gen_modpow(rng):
    m = rng.randint(3, 200); a, e = rng.randint(2, 99), rng.randint(2, 200)
    r, base, ee, steps = 1, a % m, e, []
    while ee:
        if ee & 1:
            r = r * base % m; steps.append(f"bit1: r={r}")
        base = base * base % m; ee >>= 1
    return qa(f"{a}^{e} mod {m} = ?", "square-and-multiply " + "; ".join(steps[:8]), str(pow(a, e, m)))


def gen_inverse(rng):
    m = rng.randint(3, 300); a = rng.randint(1, m - 1)
    if math.gcd(a, m) != 1:
        return qa(f"Does {a} have an inverse mod {m}?", f"gcd({a},{m})={math.gcd(a, m)}", "no")
    return qa(f"Inverse of {a} mod {m}?", f"gcd=1, so it exists; {a}*{pow(a, -1, m)}={a * pow(a, -1, m)}",
              str(pow(a, -1, m)))


def gen_primality(rng):
    n = rng.randint(2, 5000)
    if is_prime(n):
        return qa(f"Is {n} prime?", f"no divisor d with d*d <= {n}", "yes")
    f = factorize(n)
    return qa(f"Is {n} prime?", f"{n} = {_fmt_fact(f)}", "no")


def gen_factor(rng):
    n = rng.randint(2, 20000)
    return qa(f"Factor {n} into primes.", "trial division", _fmt_fact(factorize(n)))


def gen_phi_divisors(rng):
    n = rng.randint(2, 2000); f = factorize(n)
    phi = n
    for p in f: phi = phi // p * (p - 1)
    tau = 1; sigma = 1
    for p, e in f.items():
        tau *= e + 1; sigma *= (p ** (e + 1) - 1) // (p - 1)
    kind = rng.choice(["phi", "tau", "sigma"])
    ans = {"phi": phi, "tau": tau, "sigma": sigma}[kind]
    name = {"phi": "Euler phi", "tau": "number of divisors", "sigma": "sum of divisors"}[kind]
    return qa(f"{name}({n}) = ?", f"{n} = {_fmt_fact(f)}", str(ans))


def gen_crt(rng):
    ms = rng.sample([3, 4, 5, 7, 8, 9, 11, 13], 2)
    x = rng.randint(0, ms[0] * ms[1] - 1)
    return qa(f"Solve x = {x % ms[0]} (mod {ms[0]}), x = {x % ms[1]} (mod {ms[1]}).",
              f"moduli coprime, unique mod {ms[0] * ms[1]}", f"x = {x} (mod {ms[0] * ms[1]})")


def gen_fermat(rng):
    p = rng.choice([p for p in range(3, 200) if is_prime(p)]); a = rng.randint(2, p - 1)
    return qa(f"Compute {a}^{p - 1} mod {p}.", f"{p} is prime and {p} does not divide {a}", str(pow(a, p - 1, p)))


# --- stage 8 -------------------------------------------------------------------
def gen_valuation(rng):
    p = rng.choice([2, 3, 5, 7]); n = rng.randint(1, 100000)
    v = 0; m = n
    while m % p == 0: m //= p; v += 1
    return qa(f"v_{p}({n}) = ? (largest e with {p}^e dividing {n})", f"{n} = {p}^{v} * {m}", str(v))


def gen_order(rng):
    m = rng.randint(3, 120); cands = [a for a in range(2, m) if math.gcd(a, m) == 1]
    if not cands: return gen_order(rng)
    a = rng.choice(cands); k, x = 1, a % m
    while x != 1: x = x * a % m; k += 1
    return qa(f"Multiplicative order of {a} mod {m}?", f"smallest k with {a}^k = 1 mod {m}", str(k))


def gen_qr(rng):
    p = rng.choice([p for p in range(5, 120) if is_prime(p)]); a = rng.randint(1, p - 1)
    qr = any(x * x % p == a for x in range(1, p))
    leg = pow(a, (p - 1) // 2, p); leg = -1 if leg == p - 1 else leg
    return qa(f"Is {a} a square mod {p}? Give the Legendre symbol ({a}/{p}).",
              f"Euler criterion: {a}^{(p - 1) // 2} mod {p}", f"{'yes' if qr else 'no'}, symbol = {leg}")


def gen_two_squares(rng):
    n = rng.randint(2, 400)
    reps = [(a, b) for a in range(0, int(n ** .5) + 1) for b in range(a, int(n ** .5) + 1) if a * a + b * b == n]
    return qa(f"Write {n} as a^2 + b^2 with 0<=a<=b, or say none.", "search a,b",
              "; ".join(f"{a}^2+{b}^2" for a, b in reps) if reps else "none")


def gen_parity_structure(rng):
    k = rng.randint(1, 30)
    kind = rng.choice(["odd_sq", "even_sum", "mod4"])
    if kind == "odd_sq":
        n = 2 * k + 1
        return qa(f"Is {n}^2 mod 8 determined? Compute it.", f"{n} is odd, n^2 = 1 mod 8 for odd n", str(n * n % 8))
    if kind == "even_sum":
        return qa(f"Parity of {k} + {k + 1}?", "consecutive integers have opposite parity", "odd")
    n = rng.randint(1, 1000)
    return qa(f"What is {n}^2 mod 4?", "squares are 0 or 1 mod 4", str(n * n % 4))


def gen_primitive_root(rng):
    p = rng.choice([q for q in range(3, 80) if is_prime(q)])
    roots = [g for g in range(1, p) if len({pow(g, k, p) for k in range(1, p)}) == p - 1]
    return qa(f"List the primitive roots modulo {p}.", f"g is a primitive root iff its order is {p - 1}", str(roots))


def gen_wilson(rng):
    n = rng.randint(2, 30)
    f = 1
    for i in range(2, n): f = f * i % n
    return qa(f"({n - 1})! mod {n} = ? Is {n} prime?", "Wilson: (n-1)! = -1 mod n iff n is prime",
              f"{f}, {'prime' if is_prime(n) else 'not prime'}")


def gen_perfect(rng):
    n = rng.randint(2, 600)
    s = sum(d for d in range(1, n) if n % d == 0)
    return qa(f"Sum of proper divisors of {n}; deficient, perfect or abundant?", "add divisors below n",
              f"{s}, {'perfect' if s == n else 'abundant' if s > n else 'deficient'}")


def gen_crt3(rng):
    ms = rng.sample([3, 5, 7, 11, 13], 3)
    x = rng.randint(0, ms[0] * ms[1] * ms[2] - 1)
    return qa(f"Solve x = {x % ms[0]} (mod {ms[0]}), x = {x % ms[1]} (mod {ms[1]}), x = {x % ms[2]} (mod {ms[2]}).",
              "pairwise coprime", f"x = {x} (mod {ms[0] * ms[1] * ms[2]})")


def gen_nth_prime(rng):
    k = rng.randint(1, 200)
    c, n = 0, 1
    while c < k:
        n += 1
        if is_prime(n): c += 1
    return qa(f"What is the {k}-th prime?", "count primes in order", str(n))


def gen_pi_count(rng):
    n = rng.randint(10, 3000)
    return qa(f"How many primes are at most {n}?", "sieve", str(sum(1 for m in range(2, n + 1) if is_prime(m))))


def gen_pell(rng):
    d = rng.choice([x for x in range(2, 60) if int(x ** .5) ** 2 != x])
    y = 1
    while True:
        x2 = d * y * y + 1; x = int(x2 ** .5)
        if x * x == x2: break
        y += 1
        if y > 20000: return gen_pell(rng)
    return qa(f"Smallest positive solution of x^2 - {d}y^2 = 1?", "search y, test that d y^2 + 1 is a square", f"x={x}, y={y}")


def gen_gcd_lcm3(rng):
    a, b, c = (rng.randint(2, 300) for _ in range(3))
    g = math.gcd(math.gcd(a, b), c); l = a * b // math.gcd(a, b); l = l * c // math.gcd(l, c)
    return qa(f"gcd and lcm of {a}, {b}, {c}?", "fold pairwise", f"gcd={g}, lcm={l}")


GENS3 = [gen_gcd, gen_bezout, gen_modop, gen_modpow, gen_inverse, gen_primality, gen_factor,
         gen_phi_divisors, gen_crt, gen_fermat, gen_parity_structure, gen_wilson, gen_perfect, gen_crt3,
         gen_nth_prime, gen_pi_count, gen_gcd_lcm3]
GENS8 = [gen_valuation, gen_order, gen_qr, gen_two_squares, gen_primitive_root, gen_pell]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        if rng.random() < 0.7:
            g, stage = rng.choice(GENS3), 3
        else:
            g, stage = rng.choice(GENS8), 8
        yield rec(DOMAIN, g.__name__, g(rng), stage)
