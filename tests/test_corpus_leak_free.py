from blindmath.data.audit import audit_paths
from blindmath.data.build import build
from blindmath.tokenizer import MathTokenizer
from blindmath.data.shards import iter_train


def test_built_corpus_and_tokenizer_are_clean(tmp_path):
    out = str(tmp_path / "c")
    m = build(out, 3000, seed=3, include_lean=True)
    assert m["final_audit"]["flagged"] == 0
    tok = MathTokenizer.train((r.text for r in iter_train(out)), 400)
    tok.save(out + "/tokenizer.json")
    rep = audit_paths([out])
    assert rep["flagged"] == 0, rep
