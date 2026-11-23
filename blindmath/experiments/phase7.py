"""Phase 7: final experiment. The model sees only a bare Lean statement about the map `F`.

Steps
  0. sanity: the statement compiles (with `sorry` it must report exactly that warning)
  1. computation: finite exploration of F (logged as computation, never as proof)
  2. auxiliary lemmas: baseline tactics (non-AI) and model proposals, strictly verified; known results are
     logged as `rediscovery` (rule 7)
  3. main target: the model proposes proofs (Lean-repair rounds); only strict acceptance is success
The run writes ledger.jsonl (hash-chained) and report.md. No network access is used.
"""
from __future__ import annotations

import argparse
import json
import os

from blindmath.experiments import discover
from blindmath.experiments.ledger import Ledger
from blindmath.experiments.targets import AUX_LEMMAS, BASELINE_TACTICS, TARGET, LeanProblem
from blindmath.reasoning.explorer import explore
from blindmath.reasoning.search import lean_search
from blindmath.theorem.lean_runner import LeanRunner
from blindmath.theorem.library import TheoremLibrary


def check_statement(runner: LeanRunner, p: LeanProblem) -> bool:
    src = p.prelude.strip() + "\n\n" + p.header + " by sorry\n"
    r = runner.check_source(src)
    return r.reason == "uses sorry" and not any(d.severity == "error" for d in r.diagnostics)


def run(out_dir: str, ckpt: str | None, samples: int, rounds: int, upper: int, device: str = "auto",
        corpus: str | None = None, discover_limit: int = 40) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    led = Ledger(os.path.join(out_dir, "ledger.jsonl"))
    lib = TheoremLibrary(os.path.join(out_dir, "theorems"))
    if corpus:  # rule 1, checked again right before the experiment
        from blindmath.data.audit import audit_paths
        rep = audit_paths([corpus])
        led.log("computation", text="leak audit of training data before the experiment", **rep)
        if rep["flagged"]:
            raise SystemExit(f"leak audit failed: {rep}")
    runner = LeanRunner()
    result = {"lean_available": runner.available, "target_proved": False, "aux_verified": [], "aux_failed": []}
    if not runner.available:
        led.log("computation", text="Lean not available; formal steps skipped")
        _report(out_dir, result)
        return result

    result["statement_compiles"] = check_statement(runner, TARGET)
    led.log("computation", text="target statement compiles with sorry placeholder", ok=result["statement_compiles"])

    ex = explore(TARGET.py_map, 1, upper, 100_000)
    led.log("computation", text="finite exploration of F", **ex.summary())

    propose = None
    if ckpt:
        import torch  # noqa: F401
        from blindmath.reasoning.search import ModelProposer
        from blindmath.tokenizer import MathTokenizer
        from blindmath.training.train import load_model, pick_device
        dev = pick_device(device)
        model, ck = load_model(ckpt, dev)
        tok = MathTokenizer.load(os.path.join(os.path.dirname(ckpt), ck["tokenizer"]))
        proposer = ModelProposer(model, tok, dev)
        propose = lambda prompt, n: proposer.complete(prompt, n, temperature=0.8)

    # --- auxiliary lemmas ---------------------------------------------------------------
    for lem in AUX_LEMMAS:
        solved = None
        for tac in BASELINE_TACTICS:
            res = runner.verify_proof(lem.prelude, lem.header, tac)
            led.log("proof_attempt", problem=lem.name, source="baseline_tactics", proof=tac,
                    accepted=res.accepted, reason=res.reason)
            if res.accepted:
                solved = ("baseline_tactics", tac); break
        if solved is None and propose:
            out = lean_search(propose, runner, lem.prelude, lem.header, samples, rounds,
                              on_attempt=lambda a, n=lem.name: led.log("proof_attempt", problem=n, source="model", **a))
            if out.accepted:
                solved = ("model", out.proof)
        if solved:
            led.log("lean_verified", problem=lem.name, source=solved[0], proof=solved[1])
            led.log("rediscovery", problem=lem.name, note="elementary fact about F, known to the experimenter")
            lib.add_theorem(name=lem.name, prelude=lem.prelude, header=lem.header, proof=solved[1], source=solved[0],
                            axioms=runner.verify_proof(lem.prelude, lem.header, solved[1]).axioms, novelty="rediscovery")
            result["aux_verified"].append({"name": lem.name, "source": solved[0]})
        else:
            result["aux_failed"].append(lem.name)

    # --- lemma discovery: conjecture from data, test, prove; everything is recorded ---------
    result["discovery"] = discover.run(TARGET.prelude, TARGET.py_map, led, lib, runner, propose,
                                       limit=discover_limit, upper=min(upper, 3000))

    # --- main target ----------------------------------------------------------------------
    if propose:
        out = lean_search(propose, runner, TARGET.prelude, TARGET.header, samples, rounds,
                          on_attempt=lambda a: led.log("proof_attempt", problem="target", source="model", **a))
        if out.accepted:
            led.log("lean_verified", problem="target", source="model", proof=out.proof)
            lib.add_theorem(name="target", prelude=TARGET.prelude, header=TARGET.header, proof=out.proof,
                            source="model", axioms=runner.verify_proof(TARGET.prelude, TARGET.header, out.proof).axioms)
            result["target_proved"] = True
        result["target_attempts"] = len(out.attempts)
    else:
        led.log("computation", text="no checkpoint given: main target not attempted")
    lib.render_markdown()
    result["theorems_recorded"] = len(lib.entries())
    _report(out_dir, result)
    return result


def _report(out_dir: str, r: dict):
    lines = ["# Phase 7 report", "",
             f"- Lean available: {r['lean_available']}",
             f"- Target statement compiles: {r.get('statement_compiles')}",
             f"- Auxiliary lemmas verified: {[a['name'] + ' (' + a['source'] + ')' for a in r['aux_verified']]}",
             f"- Auxiliary lemmas not verified: {r['aux_failed']}",
             f"- Discovery loop: {r.get('discovery')}",
             f"- Theorems recorded in library: {r.get('theorems_recorded', 0)} (see theorems/DISCOVERIES.md)",
             f"- Model attempts on target: {r.get('target_attempts', 0)}",
             f"- **Target proved (strict Lean acceptance): {r['target_proved']}**", "",
             "Only `lean_verified` ledger entries count as formal success. Computations are not proofs."]
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="runs/phase7")
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--upper", type=int, default=5000)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--corpus", default=None, help="training corpus dir to leak-audit before the run")
    ap.add_argument("--discover-limit", type=int, default=40)
    a = ap.parse_args(argv)
    print(json.dumps(run(a.out, a.ckpt, a.samples, a.rounds, a.upper, a.device, a.corpus, a.discover_limit), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
