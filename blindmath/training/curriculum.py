"""Curriculum over the 8 stages of the research plan (section 4).

Importance -> sampling weight. Training proceeds stage by stage; stage k samples from stages <= k,
with the current stage over-weighted and earlier stages replayed so nothing is forgotten.
"""
from __future__ import annotations

# stage: (name, importance label, importance weight)
STAGES = {
    1: ("arithmetic / integers / sets", "必須", 1.0),
    2: ("logic / proof / induction", "最重要", 2.0),
    3: ("elementary number theory / congruences", "最重要", 2.0),
    4: ("algebra", "高", 1.5),
    5: ("discrete mathematics", "高", 1.5),
    6: ("analysis", "高", 1.5),
    7: ("mathematical logic", "高", 1.5),
    8: ("advanced number theory", "最重要", 2.0),
}


def stage_weights(phase: int, current_boost: float = 3.0) -> dict[int, float]:
    """Sampling weights for training phase `phase` (1..8)."""
    w = {}
    for s in range(1, phase + 1):
        base = STAGES[s][2]
        w[s] = base * (current_boost if s == phase else 1.0)
    return w


def steps_per_phase(total_steps: int) -> list[int]:
    """Split total steps over the 8 phases proportionally to importance (min 1 each)."""
    tot = sum(v[2] for v in STAGES.values())
    steps = [max(1, int(total_steps * STAGES[s][2] / tot)) for s in range(1, 9)]
    steps[-1] += max(0, total_steps - sum(steps))
    return steps


def phase_for_step(step: int, plan: list[int]) -> int:
    acc = 0
    for i, n in enumerate(plan):
        acc += n
        if step < acc:
            return i + 1
    return len(plan)
