"""Lemma discovery for a map defined in Lean: conjecture from data, test, then try to prove in Lean.

Flow per candidate: hypothesis (ledger) -> numeric test (computation, ledger) -> Lean proof attempts
(baseline tactics, optionally the model) -> lean_verified + library entry, or conjecture status recorded.
"""
from __future__ import annotations

from typing import Callable

from blindmath.experiments.ledger import Ledger
from blindmath.experiments.targets import LeanProblem
from blindmath.theorem.library import TheoremLibrary
from blindmath.theorem.lean_runner import LeanRunner

DISCOVER_TACTICS = ["by unfold F; split <;> omega", "by unfold F; omega", "by omega"]


def candidates(prelude: str, fn: Callable[[int], int], fname: str = "F", upper: int = 3000,
               moduli=(2, 3, 4, 6, 8, 16), ks=(2, 3, 4, 8)) -> list[tuple[str, LeanProblem]]:
    """(plain-text conjecture, Lean problem) pairs that hold on all tested n (finite evidence only)."""
    out, seen = [], set()
    for M in moduli:
        for R in range(M):
            ns = [n for n in range(1, upper) if n % M == R]
            vals = [fn(n) for n in ns]
            for K in ks:
                residues = {v % K for v in vals}
                if len(residues) == 1:
                    C = residues.pop()
                    name = f"{fname}_mod{M}_{R}_by{K}"
                    if (M, R, K, C) in seen:
                        continue
                    seen.add((M, R, K, C))
                    hdr = f"theorem {name} (n : Nat) (h : n % {M} = {R}) : {fname} n % {K} = {C} :="
                    out.append((f"if n = {R} mod {M} then {fname}(n) = {C} mod {K}", LeanProblem(name, prelude, hdr)))
            if all(v > n for n, v in zip(ns, vals)):
                name = f"{fname}_gt_mod{M}_{R}"
                out.append((f"if n = {R} mod {M} then {fname}(n) > n",
                            LeanProblem(name, prelude, f"theorem {name} (n : Nat) (h : n % {M} = {R}) : n < {fname} n :=")))
            if all(v < n for n, v in zip(ns, vals)):
                name = f"{fname}_lt_mod{M}_{R}"
                out.append((f"if n = {R} mod {M} (n>0) then {fname}(n) < n",
                            LeanProblem(name, prelude, f"theorem {name} (n : Nat) (h : n % {M} = {R}) (h0 : 0 < n) : {fname} n < n :=")))
    return out


def run(prelude: str, fn: Callable[[int], int], ledger: Ledger, lib: TheoremLibrary, runner: LeanRunner,
        propose=None, limit: int = 40, upper: int = 3000, known: set[str] | None = None) -> dict:
    stats = {"tried": 0, "verified": 0, "open": 0}
    for text, prob in candidates(prelude, fn, upper=upper)[:limit]:
        stats["tried"] += 1
        ledger.log("hypothesis", text=text, lean=prob.header)
        ledger.log("computation", text=f"numeric test passed for n < {upper}: {text}", note="finite evidence, not a proof")
        solved = None
        for tac in DISCOVER_TACTICS:
            res = runner.verify_proof(prob.prelude, prob.header, tac)
            ledger.log("proof_attempt", problem=prob.name, source="baseline_tactics", proof=tac,
                       accepted=res.accepted, reason=res.reason)
            if res.accepted:
                solved = ("baseline_tactics", tac, res.axioms); break
        if solved is None and propose:
            from blindmath.reasoning.search import lean_search
            out = lean_search(propose, runner, prob.prelude, prob.header, 4, 1,
                              on_attempt=lambda a, n=prob.name: ledger.log("proof_attempt", problem=n, source="model", **a))
            if out.accepted:
                res = runner.verify_proof(prob.prelude, prob.header, out.proof)
                solved = ("model", out.proof, res.axioms)
        if solved:
            nov = "rediscovery" if known and prob.name in known else "unclassified"
            ledger.log("lean_verified", problem=prob.name, source=solved[0], proof=solved[1])
            if nov == "rediscovery":
                ledger.log("rediscovery", problem=prob.name, note="in experimenter's known catalog")
            lib.add_theorem(name=prob.name, prelude=prob.prelude, header=prob.header, proof=solved[1],
                            source=solved[0], axioms=solved[2], novelty=nov)
            lib.add_conjecture(text, "proved", f"Lean-verified ({solved[0]})", prob.header)
            stats["verified"] += 1
        else:
            lib.add_conjecture(text, "numerically_supported", f"holds for n < {upper}; no Lean proof found", prob.header)
            stats["open"] += 1
    return stats
