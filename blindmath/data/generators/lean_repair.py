"""Phase 5 data: (wrong attempt, real Lean error) -> corrected proof. Requires a Lean toolchain.

A wrong attempt is produced by mutating a known-good proof; the Lean error text is the *actual* message
Lean printed for it, so the model learns to use feedback rather than to recite templates.
"""
from __future__ import annotations

import random
from typing import Iterator

from blindmath.data.generators.lean_proofs import LeanItem, iter_items
from blindmath.reasoning.prompts import clean_error
from blindmath.theorem.lean_runner import LeanRunner

from .common import rec

DOMAIN = "lean_repair"
_SWAPS = [("omega", "simp"), ("omega", "rfl"), ("simp", "rfl"), ("decide", "omega"), ("rfl", "simp"),
          ("Nat.mul_pos (Nat.succ_pos k) ih", "ih"), ("Or.inr Or.inl", "Or.inl Or.inr")]


def mutate(proof: str, rng: random.Random) -> str | None:
    opts = [(a, b) for a, b in _SWAPS if a in proof]
    if not opts:
        return None
    a, b = rng.choice(opts)
    return proof.replace(a, b, 1)


def generate(rng: random.Random, n: int, runner: LeanRunner | None = None) -> Iterator:
    runner = runner or LeanRunner(timeout=60)
    if not runner.available:
        return
    made = 0
    for it in iter_items(rng, n * 4):
        bad = mutate(it.proof, rng)
        if bad is None or bad == it.proof:
            continue
        res = runner.verify_proof(it.prelude, it.header, bad)
        if res.accepted or res.reason in ("forbidden construct in candidate", "timeout"):
            continue
        err = clean_error(res.error_text())
        text = f"Q: Lean4\n{it.prompt()}\nTry: {bad.strip()}\nError: {err}\nA: {it.proof}\n"
        yield rec(DOMAIN, f"repair_{it.family}", text, it.stage, kind="proof")
        made += 1
        if made >= n:
            return
