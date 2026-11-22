"""Lean 4 integration (Phase 5). Communication = subprocess (`lean FILE`), parsed diagnostics.

Strict acceptance (rule 6): a proof counts only if
  * Lean exits 0 with no `error` diagnostics,
  * no `sorry` warning, and
  * `#print axioms NAME` lists only the standard axioms (propext, Classical.choice, Quot.sound).
The harness fixes the prelude and the theorem *statement*; the model supplies only the text after `:=`,
and that text is screened for constructs that could change the statement or smuggle in axioms.
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field

ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
FORBIDDEN = re.compile(
    r"\b(sorry|admit|axiom|native_decide|unsafe|implemented_by|extern|macro|macro_rules|syntax|elab|"
    r"import|set_option|opaque|noncomputable|initialize|run_cmd|run_elab|namespace|section|end|open|"
    r"instance|attribute|local|scoped)\b|#\w+|/-|sorryAx|ofReduceBool", re.U)
_DIAG = re.compile(r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+): (?P<sev>error|warning|info): (?P<msg>.*)$")


def find_lean() -> str | None:
    cands = [os.environ.get("BLINDMATH_LEAN"), shutil.which("lean"),
             os.path.expanduser("~/.elan/bin/lean")] + sorted(glob.glob("/opt/lean/*/bin/lean"), reverse=True)
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


@dataclass
class Diagnostic:
    line: int
    col: int
    severity: str
    message: str


@dataclass
class LeanResult:
    accepted: bool                    # strict acceptance (rule 6)
    reason: str                       # "ok" or why not
    diagnostics: list[Diagnostic] = field(default_factory=list)
    axioms: list[str] = field(default_factory=list)
    raw: str = ""

    def error_text(self, limit: int = 400) -> str:
        errs = [f"{d.line}:{d.col} {d.message}" for d in self.diagnostics if d.severity == "error"]
        return ("; ".join(errs) or self.reason)[:limit]


class LeanRunner:
    def __init__(self, lean_path: str | None = None, timeout: float = 60.0):
        self.lean = lean_path or find_lean()
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return self.lean is not None

    def run_source(self, source: str) -> tuple[int, str]:
        if not self.available:
            raise RuntimeError("Lean 4 not found (set BLINDMATH_LEAN or install elan)")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "Check.lean")
            with open(p, "w", encoding="utf-8") as f:
                f.write(source)
            try:
                r = subprocess.run([self.lean, p], capture_output=True, text=True, timeout=self.timeout, cwd=d)
            except subprocess.TimeoutExpired:
                return 124, "timeout"
            return r.returncode, (r.stdout + r.stderr).replace(p, "Check.lean")

    @staticmethod
    def parse(output: str) -> list[Diagnostic]:
        diags, cur = [], None
        for line in output.splitlines():
            m = _DIAG.match(line)
            if m:
                cur = Diagnostic(int(m["line"]), int(m["col"]), m["sev"], m["msg"])
                diags.append(cur)
            elif cur is not None:
                cur.message += "\n" + line
        return diags

    # ---------------------------------------------------------------------------------
    def check_source(self, source: str) -> LeanResult:
        """Plain check of a complete file (no statement fixing). Used for data verification."""
        code, out = self.run_source(source)
        diags = self.parse(out)
        errs = [d for d in diags if d.severity == "error"]
        sorry = any("sorry" in d.message for d in diags if d.severity == "warning")
        if code == 124:
            return LeanResult(False, "timeout", diags, raw=out)
        if errs or code != 0:
            return LeanResult(False, "lean error", diags, raw=out)
        if sorry:
            return LeanResult(False, "uses sorry", diags, raw=out)
        return LeanResult(True, "ok", diags, raw=out)

    def verify_proof(self, prelude: str, header: str, candidate: str) -> LeanResult:
        """Strict check: fixed prelude + fixed statement header + model-written proof text."""
        if not candidate.strip():
            return LeanResult(False, "empty proof")
        if FORBIDDEN.search(candidate):
            return LeanResult(False, "forbidden construct in candidate")
        lines = candidate.rstrip().split("\n")
        if any(l and not l[0].isspace() for l in lines[1:]):
            return LeanResult(False, "continuation lines must be indented")
        m = re.search(r"\btheorem\s+([^\s(:]+)", header)
        name = m.group(1) if m else None
        src = (prelude.strip() + "\n\n" if prelude.strip() else "") + header.rstrip() + " " + candidate.strip() + "\n"
        if name:
            src += f"\n#print axioms {name}\n"
        code, out = self.run_source(src)
        diags = self.parse(out)
        if code == 124:
            return LeanResult(False, "timeout", diags, raw=out)
        errs = [d for d in diags if d.severity == "error"]
        if errs or code != 0:
            return LeanResult(False, "lean error", diags, raw=out)
        if any("sorry" in d.message for d in diags):
            return LeanResult(False, "uses sorry", diags, raw=out)
        axioms: list[str] = []
        if name:
            info = " ".join(d.message for d in diags if d.severity == "info")
            if "does not depend on any axioms" not in info:
                m2 = re.search(r"depends on axioms: \[(.*?)\]", info, re.S)
                axioms = [a.strip() for a in m2.group(1).split(",")] if m2 else ["<unparsed>"]
                bad = [a for a in axioms if a not in ALLOWED_AXIOMS]
                if bad:
                    return LeanResult(False, f"non-standard axioms: {bad}", diags, axioms, out)
        return LeanResult(True, "ok", diags, axioms, out)
