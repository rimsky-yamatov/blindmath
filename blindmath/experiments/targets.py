"""Problem definitions used ONLY at experiment time (Phases 6 and 7).

IMPORTANT: nothing in this file is ever read by the data pipeline or the tokenizer trainer.
The target is presented to the model as a bare Lean statement about an integer map named `F`:
no name, no history, no literature (rule 3: the experiment code never searches the web either).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

ITER_DEF = """def iter (f : Nat → Nat) : Nat → Nat → Nat
  | 0, n => n
  | k+1, n => iter f k (f n)"""


@dataclass
class LeanProblem:
    name: str
    prelude: str
    header: str
    py_map: Callable[[int], int] | None = None
    note: str = ""


def _F(n: int) -> int:
    return n // 2 if n % 2 == 0 else 3 * n + 1


F_PRELUDE = "def F (n : Nat) : Nat := if n % 2 = 0 then n / 2 else 3 * n + 1\n\n" + ITER_DEF

# The final statement: shown to the model as-is.
TARGET = LeanProblem(
    name="target",
    prelude=F_PRELUDE,
    header="theorem target (n : Nat) (hn : 0 < n) : ∃ k : Nat, iter F k n = 1 :=",
    py_map=_F,
)

# Small, *provable* facts about F that a research run is expected to rediscover on the way (rule 7 logs these).
AUX_LEMMAS = [
    LeanProblem("F_even", F_PRELUDE, "theorem F_even (n : Nat) (h : n % 2 = 0) : F n = n / 2 :="),
    LeanProblem("F_odd", F_PRELUDE, "theorem F_odd (n : Nat) (h : n % 2 = 1) : F n = 3 * n + 1 :="),
    LeanProblem("F_odd_even", F_PRELUDE, "theorem F_odd_even (n : Nat) (h : n % 2 = 1) : F n % 2 = 0 :="),
    LeanProblem("F_lt_even", F_PRELUDE, "theorem F_lt_even (n : Nat) (h : n % 2 = 0) (h0 : 0 < n) : F n < n :="),
    LeanProblem("F_pos", F_PRELUDE, "theorem F_pos (n : Nat) (h : 0 < n) : 0 < F n :="),
    LeanProblem("F_double", F_PRELUDE, "theorem F_double (n : Nat) : F (2 * n) = n :="),
    LeanProblem("iter_add", ITER_DEF,
                "theorem iter_add (f : Nat → Nat) (a b n : Nat) : iter f (a + b) n = iter f b (iter f a n) :="),
]

# Non-ML baseline tactics tried by the harness (logged as source=baseline_tactics, never as AI success).
BASELINE_TACTICS = [
    "by unfold F; split <;> omega",
    "by omega",
    "by simp",
    "by\n  induction a generalizing n with\n  | zero => simp [iter]\n  | succ k ih =>\n    rw [show k + 1 + b = (k + b) + 1 by omega]\n    simp only [iter]\n    exact ih (f n)",
]

# Phase 6: unknown (to the model) maps for free exploration.
UNKNOWN_MAPS = {
    "U1": ("n -> digit sum of n (base 10)", lambda n: sum(map(int, str(n)))),
    "U2": ("n -> (n*n + 7) mod 101", lambda n: (n * n + 7) % 101),
    "U3": ("n -> n - (largest square <= n)", lambda n: n - int(n ** 0.5) ** 2 if n > 0 else 0),
    "U4": ("n -> reverse(n) + n", lambda n: n + int(str(n)[::-1])),
}
