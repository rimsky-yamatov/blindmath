"""Append-only research ledger (rules 4, 5, 6, 7).

Every entry has a `kind`; kinds are never mixed:
  hypothesis     model-generated conjecture, unverified
  computation    result of running code on finite data (NOT a proof)
  proof_attempt  candidate proof text sent to Lean (any outcome)
  lean_verified  proof accepted under strict Lean acceptance (the only formal success)
  rediscovery    a verified/observed result that was already known to the experimenter
Entries are hash-chained so tampering with history is detectable.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

KINDS = {"hypothesis", "computation", "proof_attempt", "lean_verified", "rediscovery"}


class Ledger:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._prev = "0" * 64
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                if line.strip():
                    self._prev = json.loads(line)["hash"]

    def log(self, kind: str, **fields) -> dict:
        assert kind in KINDS, kind
        entry = {"t": round(time.time(), 3), "kind": kind, **fields, "prev": self._prev}
        body = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        entry["hash"] = hashlib.sha256(body.encode()).hexdigest()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._prev = entry["hash"]
        return entry

    @staticmethod
    def verify_chain(path: str) -> bool:
        prev = "0" * 64
        for line in open(path, encoding="utf-8"):
            if not line.strip():
                continue
            e = json.loads(line)
            h = e.pop("hash")
            if e["prev"] != prev:
                return False
            if hashlib.sha256(json.dumps(e, sort_keys=True, ensure_ascii=False).encode()).hexdigest() != h:
                return False
            prev = h
        return True

    @staticmethod
    def summary(path: str) -> dict:
        counts: dict[str, int] = {}
        for line in open(path, encoding="utf-8"):
            if line.strip():
                k = json.loads(line)["kind"]
                counts[k] = counts.get(k, 0) + 1
        return counts
