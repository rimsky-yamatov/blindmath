"""Prompt formats shared by data generation and search (torch-free)."""
from __future__ import annotations

import re


def clean_error(msg: str, limit: int = 160) -> str:
    msg = re.sub(r"^\d+:\d+\s*", "", msg.strip())
    return " ".join(msg.split())[:limit]


def first_prompt(prelude: str, header: str) -> str:
    return "Q: Lean4\n" + ((prelude.strip() + "\n") if prelude.strip() else "") + header.rstrip() + "\nA:"


def repair_prompt(prelude: str, header: str, attempt: str, error: str) -> str:
    base = first_prompt(prelude, header)[: -len("\nA:")]
    return f"{base}\nTry: {attempt.strip()}\nError: {clean_error(error)}\nA:"
