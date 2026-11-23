"""`python -m blindmath.cli <command>`: one entry point for every phase."""
from __future__ import annotations

import sys

COMMANDS = {
    "build-data": ("blindmath.data.build", "Phase 2: generate + audit + split the corpus"),
    "audit": ("blindmath.cli_audit", "Rule 1: scan files/directories for target-problem leakage"),
    "train-tokenizer": ("blindmath.training.train_tokenizer", "Phase 1: train the tokenizer on the corpus"),
    "train": ("blindmath.training.train", "Phase 3/4: pre-train with the curriculum"),
    "eval": ("blindmath.evaluation.benchmark", "Phase 4: held-out exact-match benchmark"),
    "lean-eval": ("blindmath.evaluation.lean_benchmark", "Phase 5: Lean-verified proof benchmark (pass@k)"),
    "expert-iter": ("blindmath.training.expert_iteration", "Self-play: keep Lean-verified model proofs as data"),
    "verify-lean-data": ("blindmath.theorem.verify_templates", "Phase 5: machine-check Lean training templates"),
    "phase6": ("blindmath.experiments.phase6", "Phase 6: study unknown maps"),
    "phase7": ("blindmath.experiments.phase7", "Phase 7: final experiment (bare Lean statement)"),
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in COMMANDS:
        print("usage: python -m blindmath.cli <command> [args]\n")
        for k, (_, d) in COMMANDS.items():
            print(f"  {k:18s} {d}")
        return 0 if not argv else 2
    import importlib
    mod = importlib.import_module(COMMANDS[argv[0]][0])
    if argv[0] == "train":
        import argparse
        ap = argparse.ArgumentParser(); mod.add_args(ap)
        mod.train(ap.parse_args(argv[1:]))
        return 0
    return mod.main(argv[1:]) or 0


if __name__ == "__main__":
    raise SystemExit(main())
