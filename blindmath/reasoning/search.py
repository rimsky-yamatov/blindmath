"""Proof search (Phase 5): sample candidates from the model, verify with Lean, repair from error feedback.

Prompt formats match the training data:
    Q: Lean4\n<prelude + header>\nA:                           (first attempt)
    Q: Lean4\n<prelude + header>\nTry: <proof>\nError: <msg>\nA:   (repair rounds)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

import torch

from blindmath.theorem.lean_runner import LeanResult, LeanRunner


class ModelProposer:
    def __init__(self, model, tok, device, max_new: int = 200):
        self.model, self.tok, self.device, self.max_new = model, tok, device, max_new

    @torch.no_grad()
    def complete(self, prompt: str, n: int = 1, temperature: float = 0.8, top_k: int = 20) -> list[str]:
        out = []
        for i in range(n):
            ids = torch.tensor([self.tok.encode(prompt, bos=True)], device=self.device)
            gen = self.model.generate(ids, self.max_new, temperature=0.0 if (n == 1 and i == 0 and temperature == 0) else temperature,
                                      top_k=top_k, stop_ids=(self.tok.eos_id,))
            out.append(self.tok.decode(gen[0, ids.size(1):].tolist()).split("\nQ:")[0].strip())
        return out


def clean_error(msg: str, limit: int = 160) -> str:
    msg = re.sub(r"^\d+:\d+\s*", "", msg.strip())
    return " ".join(msg.split())[:limit]


def first_prompt(prelude: str, header: str) -> str:
    return "Q: Lean4\n" + ((prelude.strip() + "\n") if prelude.strip() else "") + header.rstrip() + "\nA:"


def repair_prompt(prelude: str, header: str, attempt: str, error: str) -> str:
    base = first_prompt(prelude, header)[: -len("\nA:")]
    return f"{base}\nTry: {attempt.strip()}\nError: {clean_error(error)}\nA:"


@dataclass
class SearchOutcome:
    accepted: bool
    proof: str | None
    attempts: list[dict]


def lean_search(propose: Callable[[str, int], list[str]], runner: LeanRunner, prelude: str, header: str,
                samples: int = 8, rounds: int = 2, on_attempt: Callable[[dict], None] | None = None) -> SearchOutcome:
    """`propose(prompt, n)` returns n candidate proof strings. Only strict Lean acceptance counts."""
    attempts: list[dict] = []
    prompts = [first_prompt(prelude, header)]
    for rnd in range(rounds + 1):
        next_prompts: list[str] = []
        for pr in prompts:
            for cand in propose(pr, samples):
                res: LeanResult = runner.verify_proof(prelude, header, cand)
                rec = {"round": rnd, "candidate": cand, "accepted": res.accepted, "reason": res.reason,
                       "error": res.error_text(200)}
                attempts.append(rec)
                if on_attempt:
                    on_attempt(rec)
                if res.accepted:
                    return SearchOutcome(True, cand, attempts)
                if len(next_prompts) < 4 and cand.strip():
                    next_prompts.append(repair_prompt(prelude, header, cand, res.error_text()))
        prompts = next_prompts or prompts
    return SearchOutcome(False, None, attempts)
