from blindmath.tokenizer import MathTokenizer

CORPUS = ["Q: 12 + 34 = ?\nWork: 2+4=6\nA: 46\n", "Q: gcd(12, 18) = ?\nA: 6\n"] * 20


def test_roundtrip_and_digits_atomic():
    tok = MathTokenizer.train(CORPUS, vocab_size=200)
    s = "Q: 12 + 34 = ?\nA: 46\n"
    ids = tok.encode(s)
    assert tok.decode(ids) == s
    # each digit is a single token
    assert len(tok.encode("123")) == 3


def test_save_load(tmp_path):
    tok = MathTokenizer.train(CORPUS, vocab_size=200)
    p = tmp_path / "tok.json"; tok.save(str(p))
    tok2 = MathTokenizer.load(str(p))
    assert tok2.encode("gcd(12, 18)") == tok.encode("gcd(12, 18)")
