"""Stage 2 (logic/proof/induction) and stage 7 (mathematical logic: recursion, normal forms)."""
from __future__ import annotations

import itertools
import random
from typing import Iterator

from .common import rec, qa

DOMAIN = "logic"


def _rand_formula(rng, vars_, depth):
    if depth == 0 or rng.random() < 0.25:
        v = rng.choice(vars_)
        return (v, lambda env, v=v: env[v])
    op = rng.choice(["and", "or", "not", "imp", "xor"])
    if op == "not":
        s, f = _rand_formula(rng, vars_, depth - 1)
        return (f"~{s}", lambda env, f=f: not f(env))
    ls, lf = _rand_formula(rng, vars_, depth - 1)
    rs, rf = _rand_formula(rng, vars_, depth - 1)
    sym = {"and": "&", "or": "|", "imp": "->", "xor": "^"}[op]
    fn = {"and": lambda a, b: a and b, "or": lambda a, b: a or b,
          "imp": lambda a, b: (not a) or b, "xor": lambda a, b: a != b}[op]
    return (f"({ls} {sym} {rs})", lambda env, lf=lf, rf=rf, fn=fn: fn(lf(env), rf(env)))


def gen_truth_table(rng):
    vs = ["p", "q", "r"][: rng.randint(2, 3)]
    s, f = _rand_formula(rng, vs, 3)
    rows, vals = [], []
    for bits in itertools.product([False, True], repeat=len(vs)):
        env = dict(zip(vs, bits))
        v = f(env); vals.append(v)
        rows.append("".join("T" if b else "F" for b in bits) + f":{'T' if v else 'F'}")
    verdict = "tautology" if all(vals) else ("contradiction" if not any(vals) else "contingent")
    return qa(f"Classify {s} (tautology, contradiction, or contingent).", " ".join(rows), verdict)


def gen_quantifier(rng):
    dom = list(range(1, rng.randint(5, 12)))
    m = rng.randint(2, 5)
    pred = rng.choice([(f"x % {m} == 0", lambda x: x % m == 0), (f"x > {m}", lambda x: x > m),
                       (f"x*x < {m * 5}", lambda x: x * x < m * 5)])
    kind = rng.choice(["forall", "exists"])
    vals = [pred[1](x) for x in dom]
    truth = all(vals) if kind == "forall" else any(vals)
    w = ""
    if kind == "forall" and not truth:
        w = f" counterexample x={dom[vals.index(False)]}"
    if kind == "exists" and truth:
        w = f" witness x={dom[vals.index(True)]}"
    sym = "for all" if kind == "forall" else "there exists"
    return qa(f"Domain {{1..{dom[-1]}}}. Is it true that {sym} x: {pred[0]}?", "check each x" + w,
              "true" if truth else "false")


def gen_induction_check(rng):
    """Induction schema with base/step verified numerically on instances."""
    forms = [
        ("1+2+...+n = n(n+1)/2", lambda n: sum(range(1, n + 1)), lambda n: n * (n + 1) // 2),
        ("1+3+...+(2n-1) = n^2", lambda n: sum(2 * i - 1 for i in range(1, n + 1)), lambda n: n * n),
        ("2^0+2^1+...+2^(n-1) = 2^n - 1", lambda n: sum(2 ** i for i in range(n)), lambda n: 2 ** n - 1),
        ("1^2+...+n^2 = n(n+1)(2n+1)/6", lambda n: sum(i * i for i in range(1, n + 1)),
         lambda n: n * (n + 1) * (2 * n + 1) // 6),
    ]
    s, lhs, rhs = rng.choice(forms)
    n = rng.randint(1, 12)
    return qa(f"Claim P(n): {s}. Check the base case and the step n={n} -> {n + 1}.",
              f"base n=1: lhs={lhs(1)} rhs={rhs(1)}; n={n}: lhs={lhs(n)} rhs={rhs(n)}; "
              f"n={n + 1}: lhs={lhs(n + 1)} rhs={rhs(n + 1)}; lhs(n+1)=lhs(n)+term",
              "P holds on these instances; the induction step adds the same term to both sides")


def gen_demorgan_sets(rng):
    U = set(range(1, 9)); A = set(rng.sample(sorted(U), 4)); B = set(rng.sample(sorted(U), 3))
    lhs = U - (A | B); rhs = (U - A) & (U - B)
    return qa(f"U={{1..8}}, A={sorted(A)}, B={sorted(B)}. Verify complement(A union B) = complement(A) intersect complement(B).",
              f"lhs={sorted(lhs)}; rhs={sorted(rhs)}", "equal" if lhs == rhs else "not equal")


# --- stage 7: recursion / unfolding / normal forms -------------------------------------
def _unary_add(a, b):
    steps, cur = [], b
    for i in range(a):
        cur += 1
        steps.append(f"S(...)->{cur}")
    return steps, a + b


def gen_peano(rng):
    a, b = rng.randint(0, 5), rng.randint(0, 5)
    op = rng.choice(["add", "mul"])
    if op == "add":
        return qa(f"Peano: add(0,n)=n, add(S(m),n)=S(add(m,n)). Compute add({a},{b}).",
                  f"apply the second rule {a} times, each wraps one S", str(a + b))
    return qa(f"Peano: mul(0,n)=0, mul(S(m),n)=add(n,mul(m,n)). Compute mul({a},{b}).",
              f"mul({a},{b}) = {' + '.join([str(b)] * a) if a else '0'}", str(a * b))


def gen_cnf(rng):
    s, f = _rand_formula(rng, ["p", "q"], 2)
    minterms = [(p, q) for p in (False, True) for q in (False, True) if f({"p": p, "q": q})]
    dnf = " | ".join("(" + ("p" if p else "~p") + " & " + ("q" if q else "~q") + ")" for p, q in minterms) or "F"
    return qa(f"Give the disjunctive normal form (full minterms) of {s}.",
              f"true rows: {minterms}", dnf)


def gen_primitive_recursion(rng):
    k = rng.randint(0, 8)
    kind = rng.choice(["fact", "fib", "pred"])
    if kind == "fact":
        v = 1
        for i in range(2, k + 1): v *= i
        return qa(f"f(0)=1, f(S(n))=S(n)*f(n). Compute f({k}).", "unfold the recursion", str(v))
    if kind == "fib":
        a, b = 0, 1
        for _ in range(k): a, b = b, a + b
        return qa(f"g(0)=0, g(1)=1, g(n+2)=g(n)+g(n+1). Compute g({k}).", "unfold", str(a))
    return qa(f"pred(0)=0, pred(S(n))=n. Compute pred({k}).", "", str(max(k - 1, 0)))


GENS2 = [gen_truth_table, gen_quantifier, gen_induction_check, gen_demorgan_sets]
GENS7 = [gen_peano, gen_cnf, gen_primitive_recursion]


def generate(rng: random.Random, n: int) -> Iterator:
    for _ in range(n):
        if rng.random() < 0.6:
            g = rng.choice(GENS2); stage = 2
        else:
            g = rng.choice(GENS7); stage = 7
        yield rec(DOMAIN, g.__name__, g(rng), stage)
