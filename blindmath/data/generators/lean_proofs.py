"""Stage 2/3/5/8: Lean 4 (core, no Mathlib) statement/proof pairs from parameterised templates.

Every template is checked against a real Lean 4 toolchain by `blindmath.theorem.verify_templates`
(tests/test_lean_templates.py runs it when `lean` is available), so training proofs are
machine-verified, not merely plausible text.

Text format (statement/prelude = prompt, proof = target):
    Q: Lean4 <prelude lines...> theorem NAME ... :=
    A: by omega
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Iterator

from .common import rec

DOMAIN = "lean_proofs"


@dataclass
class LeanItem:
    prelude: str   # definitions needed by the statement ("" if none)
    header: str    # "theorem NAME (..) : .. :="
    proof: str     # text after ":=" (starts with "by ..." or a term)
    stage: int
    family: str

    def prompt(self) -> str:
        p = (self.prelude.strip() + "\n") if self.prelude.strip() else ""
        return p + self.header

    def source(self) -> str:
        return self.prelude.strip() + ("\n\n" if self.prelude.strip() else "") + self.header + " " + self.proof + "\n"

    def text(self) -> str:
        return f"Q: Lean4\n{self.prompt()}\nA: {self.proof}\n"


def _name(rng, base):
    return f"{base}_{rng.randint(0, 10 ** 6)}"


# ---- A: closed numeric facts by evaluation ---------------------------------------------
def fam_numeric(rng):
    a, b, c = rng.randint(2, 500), rng.randint(2, 500), rng.randint(1, 50)
    kind = rng.choice(["mul_add", "mod", "gcd", "dvd", "ndvd", "pow"])
    n = _name(rng, "num")
    if kind == "mul_add":
        h, pf = f"example : {a} * {b} + {c} = {a * b + c} :=", "by decide"
    elif kind == "mod":
        m = rng.randint(2, 30); h, pf = f"example : {a * b} % {m} = {a * b % m} :=", "by decide"
    elif kind == "gcd":
        h, pf = f"example : Nat.gcd {a} {b} = {math.gcd(a, b)} :=", "by decide"
    elif kind == "dvd":
        d = rng.randint(2, 30); h, pf = f"example : {d} ∣ {d * a} :=", f"⟨{a}, rfl⟩"
    elif kind == "ndvd":
        d = rng.randint(2, 30)
        if (a * 7 + 1) % d == 0: a += 1
        h, pf = f"example : ¬ ({d} ∣ {a * 7 + 1}) :=" if (a * 7 + 1) % d else f"example : {d} ∣ {a * 7 + 1} :=", "by decide" if (a * 7 + 1) % d else "by decide"
    else:
        x, e = rng.randint(2, 9), rng.randint(2, 8); h, pf = f"example : {x} ^ {e} = {x ** e} :=", "by decide"
    return LeanItem("", h, pf, 1 if kind in ("mul_add", "pow") else 3, "numeric")


# ---- B: omega: linear arithmetic with literal moduli ------------------------------------
def fam_omega(rng):
    n = _name(rng, "lin")
    m = rng.randint(2, 12); r = rng.randint(0, m - 1); k = rng.randint(1, 20)
    kind = rng.choice(["shift", "closed_add", "mono", "sub", "refine", "double"])
    if kind == "shift":
        h = f"theorem {n} (n : Nat) (h : n % {m} = {r}) : (n + {k}) % {m} = {(r + k) % m} :="
    elif kind == "closed_add":
        h = f"theorem {n} (a b : Nat) (ha : a % {m} = 0) (hb : b % {m} = 0) : (a + b) % {m} = 0 :="
    elif kind == "mono":
        c = rng.randint(1, 9); h = f"theorem {n} (a b : Nat) (h : a ≤ b) : a * {c} ≤ b * {c} :="
    elif kind == "sub":
        h = f"theorem {n} (a b : Nat) (h : a ≤ b) : a + (b - a) = b :="
    elif kind == "refine":
        m2 = rng.randint(2, 6); h = f"theorem {n} (n : Nat) (h : n % {m * m2} = {r}) : n % {m} = {r % m} :="
    else:
        c = rng.randint(2, 9); h = f"theorem {n} (n : Nat) : {c} * n + {c} * n = {2 * c} * n :="
    return LeanItem("", h, "by omega", 3, "omega")


# ---- C: induction over small recursive definitions --------------------------------------
def fam_induction(rng):
    t = _name(rng, "f")
    kind = rng.choice(["affine", "sum", "odd", "pow2_pos", "pow2_gt", "fact_pos"])
    if kind == "affine":
        b, c = rng.randint(0, 9), rng.randint(1, 9)
        pre = f"def {t} : Nat → Nat\n  | 0 => {b}\n  | n+1 => {t} n + {c}"
        hd = f"theorem {t}_eq (n : Nat) : {t} n = {b} + {c} * n :="
        pf = f"by\n  induction n with\n  | zero => rfl\n  | succ k ih => simp only [{t}]; omega"
        return LeanItem(pre, hd, pf, 2, "induction_affine")
    if kind == "sum":
        pre = f"def {t} : Nat → Nat\n  | 0 => 0\n  | n+1 => {t} n + (n+1)"
        hd = f"theorem {t}_formula (n : Nat) : 2 * {t} n = n * (n + 1) :="
        pf = (f"by\n  induction n with\n  | zero => rfl\n  | succ k ih =>\n    simp only [{t}]\n"
              f"    rw [Nat.mul_add, ih]\n    simp only [Nat.mul_add, Nat.add_mul, Nat.mul_one, Nat.one_mul]\n    omega")
        return LeanItem(pre, hd, pf, 2, "induction_sum")
    if kind == "odd":
        pre = f"def {t} : Nat → Nat\n  | 0 => 0\n  | n+1 => {t} n + (2*n+1)"
        hd = f"theorem {t}_sq (n : Nat) : {t} n = n * n :="
        pf = (f"by\n  induction n with\n  | zero => rfl\n  | succ k ih =>\n    simp only [{t}]\n    rw [ih]\n"
              f"    simp only [Nat.mul_add, Nat.add_mul, Nat.mul_one, Nat.one_mul]\n    omega")
        return LeanItem(pre, hd, pf, 2, "induction_odd")
    if kind in ("pow2_pos", "pow2_gt"):
        pre = f"def {t} : Nat → Nat\n  | 0 => 1\n  | n+1 => 2 * {t} n"
        if kind == "pow2_pos":
            hd = f"theorem {t}_pos (n : Nat) : 0 < {t} n :="
        else:
            hd = f"theorem {t}_gt (n : Nat) : n < {t} n :="
        pf = f"by\n  induction n with\n  | zero => decide\n  | succ k ih => simp only [{t}]; omega"
        return LeanItem(pre, hd, pf, 2, "induction_pow2")
    pre = f"def {t} : Nat → Nat\n  | 0 => 1\n  | n+1 => (n+1) * {t} n"
    hd = f"theorem {t}_pos (n : Nat) : 0 < {t} n :="
    pf = (f"by\n  induction n with\n  | zero => decide\n  | succ k ih =>\n    simp only [{t}]\n"
          f"    exact Nat.mul_pos (Nat.succ_pos k) ih")
    return LeanItem(pre, hd, pf, 2, "induction_fact")


# ---- D: lists --------------------------------------------------------------------------
def fam_lists(rng):
    n = _name(rng, "lst")
    kind = rng.choice(["len_append", "rev_rev", "len_map", "append_nil", "len_rev"])
    if kind == "len_append":
        return LeanItem("", f"theorem {n} (xs ys : List Nat) : (xs ++ ys).length = xs.length + ys.length :=", "by simp", 5, "lists")
    if kind == "rev_rev":
        return LeanItem("", f"theorem {n} (xs : List Nat) : xs.reverse.reverse = xs :=", "by simp", 5, "lists")
    if kind == "len_map":
        return LeanItem("", f"theorem {n} (f : Nat → Nat) (xs : List Nat) : (xs.map f).length = xs.length :=", "by simp", 5, "lists")
    if kind == "append_nil":
        return LeanItem("", f"theorem {n} (xs : List Nat) : xs ++ [] = xs :=", "by simp", 5, "lists")
    return LeanItem("", f"theorem {n} (xs : List Nat) : xs.reverse.length = xs.length :=", "by simp", 5, "lists")


# ---- E: propositional logic -------------------------------------------------------------
def fam_logic(rng):
    n = _name(rng, "prop")
    items = [
        (f"theorem {n} (p q : Prop) : p ∧ q → q ∧ p :=", "fun ⟨hp, hq⟩ => ⟨hq, hp⟩"),
        (f"theorem {n} (p q : Prop) : p ∨ q → q ∨ p :=", "fun h => h.elim Or.inr Or.inl"),
        (f"theorem {n} (p q : Prop) : (p → q) → ¬q → ¬p :=", "fun h hq hp => hq (h hp)"),
        (f"theorem {n} (p q r : Prop) : (p → q) → (q → r) → p → r :=", "fun f g x => g (f x)"),
        (f"theorem {n} (p : Prop) : p → ¬¬p :=", "fun hp hn => hn hp"),
        (f"theorem {n} (p q : Prop) : ¬(p ∨ q) → ¬p ∧ ¬q :=", "fun h => ⟨fun hp => h (Or.inl hp), fun hq => h (Or.inr hq)⟩"),
        (f"theorem {n} (p q : Prop) : p ∧ q → p :=", "fun h => h.1"),
        (f"theorem {n} (α : Type) (P : α → Prop) : (∀ x, P x) → ∀ y, P y :=", "fun h y => h y"),
    ]
    h, pf = rng.choice(items)
    return LeanItem("", h, pf, 2, "logic")


FAMILIES: list[Callable] = [fam_numeric, fam_omega, fam_induction, fam_lists, fam_logic]
WEIGHTS = [2, 3, 3, 1, 1]


def iter_items(rng: random.Random, n: int) -> Iterator[LeanItem]:
    for _ in range(n):
        yield rng.choices(FAMILIES, WEIGHTS)[0](rng)


def generate(rng: random.Random, n: int) -> Iterator:
    for it in iter_items(rng, n):
        yield rec(DOMAIN, it.family, it.text(), it.stage, kind="proof")
