import json

from blindmath.experiments.ledger import Ledger


def test_chain_and_tamper_detection(tmp_path):
    p = str(tmp_path / "l.jsonl")
    L = Ledger(p)
    L.log("hypothesis", text="h1")
    L.log("computation", text="checked n<1000")
    L.log("lean_verified", theorem="t")
    assert Ledger.verify_chain(p)
    assert Ledger.summary(p) == {"hypothesis": 1, "computation": 1, "lean_verified": 1}
    lines = open(p).read().splitlines()
    e = json.loads(lines[1]); e["text"] = "forged"
    lines[1] = json.dumps(e)
    open(p, "w").write("\n".join(lines) + "\n")
    assert not Ledger.verify_chain(p)
