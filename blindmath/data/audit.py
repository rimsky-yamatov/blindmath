"""Leak audit (rule 1): keep the target problem out of the training data.

Two layers:
  1. term list  - names/words that identify the target problem or its literature
  2. structure  - algebraic fingerprints of the target map (and close relatives)

Anything flagged is dropped from the corpus and logged to a quarantine file.
Note: this module necessarily contains the fingerprints, so it is part of the
code base and must never be fed to the model as data.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Iterable, Iterator

# Names / terms (compared after NFKC + casefold + whitespace removal)
FORBIDDEN_TERMS = [
    "collatz", "コラッツ", "こらっつ",
    "hailstone", "ひょう", "ヘイルストーン",
    "ulamconjecture", "ulam予想", "kakutani", "角谷", "かくたに",
    "syracuseconjecture", "syracuseproblem", "syracuse予想", "シラキュース",
    "thwaites", "hasse'salgorithm", "wondrousnumber", "hotpo",
    "halfortripleplusone", "stoppingtime", "totalstopping",
    "3n+1problem", "3x+1problem", "3n+1予想", "3x+1予想",
    "erdosmathematicsisnotyetready", "mathematicsisnotyetready",
    "lotharcollatz", "ウラム予想", "ハッセ", "ウラム", "雹", "ひょう予想", "シラキュース問題",
    "collatzlike", "ulam's", "ulamproblem", "syracuse",
    # generic "famous open problem" vocabulary is kept out of the corpus as well
    "unsolvedproblem", "openproblem", "conjecture", "未解決", "予想",
]
# "ひょう" alone is a common word (表, 票...) -> keep only the katakana/english forms.
FORBIDDEN_TERMS = [t for t in FORBIDDEN_TERMS if t != "ひょう"]

_VAR = r"[a-z](?:[a-z0-9_]{0,3})?(?:\([a-z0-9_]{1,3}\))?"
STRUCTURAL_PATTERNS = {
    # 3n+1, 3*n+1, 3x_k+1, 5n+1 ... (affine map "k*n+1" with k>=3)
    "affine_k_n_plus_1": re.compile(rf"(?<![0-9])[3-9]\*?{_VAR}\+1(?![0-9])"),
    "affine_1_plus_k_n": re.compile(rf"(?<![0-9])1\+[3-9]\*?{_VAR}(?![0-9a-z])"),
    # numeric instances like 3*7+1 (only with explicit '*' to avoid 37+1)
    "numeric_3_times_plus_1": re.compile(r"(?<![0-9])3\*[0-9]+\+1(?![0-9])"),
    "numeric_3_times_plus_1_rev": re.compile(r"(?<![0-9])1\+3\*[0-9]+(?![0-9])"),
    # "reaches 1" style statements about iteration
    "reaches_one": re.compile(r"(reach(es|ed)?|eventuallyreach|到達|到る)[^.\n]{0,12}(?<![0-9])1(?![0-9])"),
    "one_reached": re.compile(r"(?<![0-9])1(に到達|になる|へ到達|に収束)"),
}


@dataclass
class Finding:
    layer: str      # "term" | "structure"
    rule: str
    snippet: str


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).casefold()
    t = t.replace("×", "*").replace("·", "*").replace("∗", "*").replace("⋅", "*")
    t = t.replace("−", "-").replace("＋", "+")
    t = re.sub(r"\\cdot|\\times", "*", t)
    t = re.sub(r"[\s{}$]", "", t)
    return t


def audit_text(text: str) -> list[Finding]:
    norm = normalize(text)
    out: list[Finding] = []
    for term in FORBIDDEN_TERMS:
        if term in norm:
            out.append(Finding("term", term, term))
    for name, pat in STRUCTURAL_PATTERNS.items():
        m = pat.search(norm)
        if m:
            out.append(Finding("structure", name, m.group(0)))
    # co-occurrence: halving + affine odd branch is the target's fingerprint
    if re.search(rf"{_VAR}/2", norm) and re.search(rf"[3-9]\*?{_VAR}[+-][0-9]", norm) and \
            re.search(r"(even|odd|偶数|奇数|%2|mod2)", norm):
        out.append(Finding("structure", "halve_and_affine_odd_branch", "n/2 & k*n+c & parity"))
    return out


@dataclass
class AuditReport:
    scanned: int = 0
    flagged: int = 0
    by_rule: dict | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def filter_clean(records: Iterable, quarantine_path: str | None = None) -> Iterator:
    """Yield records that pass the audit; log the rest to `quarantine_path`."""
    qf = open(quarantine_path, "w", encoding="utf-8") if quarantine_path else None
    try:
        for r in records:
            findings = audit_text(r.text)
            if findings:
                if qf:
                    qf.write(json.dumps({"generator": r.generator,
                                         "findings": [asdict(f) for f in findings],
                                         "text": r.text}, ensure_ascii=False) + "\n")
                continue
            yield r
    finally:
        if qf:
            qf.close()


def audit_records(records: Iterable) -> AuditReport:
    rep = AuditReport(by_rule={})
    for r in records:
        rep.scanned += 1
        fs = audit_text(r.text)
        if fs:
            rep.flagged += 1
            for f in fs:
                rep.by_rule[f.rule] = rep.by_rule.get(f.rule, 0) + 1
    return rep


def audit_paths(paths: list[str]) -> dict:
    """Scan every text/JSON/JSONL file under `paths` (incl. tokenizer vocab); returns a summary dict."""
    import os
    scanned = flagged = 0
    examples: list[str] = []
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, fs in os.walk(p):
                files += [os.path.join(root, f) for f in fs if f.endswith((".jsonl", ".json", ".txt", ".md", ".lean"))]
        elif os.path.exists(p):
            files.append(p)
    for f in files:
        with open(f, encoding="utf-8", errors="replace") as fh:
            if f.endswith("quarantine.jsonl"):
                continue  # the quarantine file records dropped (flagged) text by design
            for line in fh:
                scanned += 1
                if audit_text(line):
                    flagged += 1
                    if len(examples) < 3:
                        examples.append(f"{os.path.basename(f)}: {line[:80]!r}")
    return {"files": len(files), "scanned": scanned, "flagged": flagged, "examples": examples}
