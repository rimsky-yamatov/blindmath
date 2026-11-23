"""Library of everything found during research: Lean-verified theorems and conjectures (rule 7).

theorems/index.jsonl      one JSON per Lean-verified theorem (statement, proof, source, axioms, novelty)
theorems/lean/NAME.lean   the exact source Lean accepted, with a provenance header
theorems/conjectures.jsonl  conjectures with status (numerically_supported / refuted / proved)
DISCOVERIES.md            human-readable summary (regenerate with render_markdown)
`novelty` is "rediscovery" only when the statement is in the experimenter's known catalog; otherwise
"unclassified" (automatic novelty claims are never made).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time


def _key(prelude: str, header: str) -> str:
    norm = re.sub(r"\s+", " ", prelude + "\n" + header).strip()
    return hashlib.sha1(norm.encode()).hexdigest()[:16]


class TheoremLibrary:
    def __init__(self, root: str):
        self.root = root
        self.lean_dir = os.path.join(root, "lean")
        os.makedirs(self.lean_dir, exist_ok=True)
        self.index_path = os.path.join(root, "index.jsonl")
        self.conj_path = os.path.join(root, "conjectures.jsonl")
        self._keys = {e["key"] for e in self.entries()}

    def entries(self) -> list[dict]:
        if not os.path.exists(self.index_path):
            return []
        return [json.loads(l) for l in open(self.index_path, encoding="utf-8") if l.strip()]

    def add_theorem(self, *, name: str, prelude: str, header: str, proof: str, source: str,
                    axioms: list[str], novelty: str = "unclassified", note: str = "") -> dict | None:
        key = _key(prelude, header)
        if key in self._keys:
            return None
        self._keys.add(key)
        src = (prelude.strip() + "\n\n" if prelude.strip() else "") + header.rstrip() + " " + proof.strip() + "\n"
        safe = re.sub(r"[^A-Za-z0-9_]", "_", name)
        with open(os.path.join(self.lean_dir, f"{safe}_{key[:6]}.lean"), "w", encoding="utf-8") as f:
            f.write(f"-- verified by Lean 4 (strict acceptance). source={source} novelty={novelty}\n")
            f.write(f"-- axioms: {axioms}\n{src}")
        e = {"key": key, "name": name, "statement": header.strip(), "prelude": prelude.strip(),
             "proof": proof.strip(), "source": source, "axioms": axioms, "novelty": novelty,
             "note": note, "t": round(time.time(), 3)}
        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        return e

    def add_conjecture(self, text: str, status: str, evidence: str = "", lean_statement: str = "") -> dict:
        assert status in {"numerically_supported", "refuted", "proved", "open"}
        e = {"text": text, "status": status, "evidence": evidence, "lean_statement": lean_statement,
             "t": round(time.time(), 3)}
        with open(self.conj_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        return e

    def conjectures(self) -> list[dict]:
        if not os.path.exists(self.conj_path):
            return []
        return [json.loads(l) for l in open(self.conj_path, encoding="utf-8") if l.strip()]

    def render_markdown(self, path: str | None = None) -> str:
        th, cj = self.entries(), self.conjectures()
        out = ["# Discoveries", "", f"Lean-verified theorems: {len(th)}  |  conjectures logged: {len(cj)}", ""]
        out += ["## Verified theorems (strict Lean acceptance)", ""]
        for e in th:
            out.append(f"- `{e['statement']}`  \n  proof: `{e['proof'].splitlines()[0]}` — source: {e['source']}, novelty: {e['novelty']}")
        out += ["", "## Conjectures (NOT theorems unless status=proved)", ""]
        for e in cj:
            out.append(f"- [{e['status']}] {e['text']}")
        md = "\n".join(out) + "\n"
        with open(path or os.path.join(self.root, "DISCOVERIES.md"), "w", encoding="utf-8") as f:
            f.write(md)
        return md
