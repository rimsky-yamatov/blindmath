from __future__ import annotations

from blindmath.data.schema import Record, LICENSE_SELF_GENERATED


def rec(domain: str, gen: str, text: str, stage: int, kind: str = "computation") -> Record:
    return Record(domain=domain, generator=gen,
                  source=f"synthetic:blindmath.data.generators.{domain}",
                  license=LICENSE_SELF_GENERATED, text=text, stage=stage, kind=kind)


def qa(question: str, steps: str, answer: str) -> str:
    """Uniform Q/work/A format used by training and evaluation."""
    body = f"Q: {question}\n"
    if steps:
        body += f"Work: {steps}\n"
    return body + f"A: {answer}\n"
