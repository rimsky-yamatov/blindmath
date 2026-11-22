import pytest
from blindmath.data.audit import audit_text

LEAKS = [
    "Collatz conjecture", "コラッツ予想", "f(n)=n/2 if n even else 3n+1", "3 * n + 1",
    "(3x_k + 1)/2", "if n is odd then 5n+1 and n/2 if even", "3*7+1 = 22",
    "the sequence reaches 1", "1に到達する", "ｎ＝３ｎ＋１", "hailstone sequence",
]
CLEAN = ["2n+1 is odd", "37+1=38", "gcd(12,18)=6", "n/2 for even n", "sum of digits of 123 is 6"]


@pytest.mark.parametrize("t", LEAKS)
def test_leaks_are_flagged(t):
    assert audit_text(t)


@pytest.mark.parametrize("t", CLEAN)
def test_clean_text_passes(t):
    assert not audit_text(t)
