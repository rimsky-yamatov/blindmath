import pytest

from blindmath.theorem import LeanRunner

pytestmark = pytest.mark.skipif(not LeanRunner().available, reason="Lean 4 not installed")
R = LeanRunner()
H = "theorem foo (n : Nat) (h : n % 2 = 1) : (n + 1) % 2 = 0 :="


def test_accepts_valid_proof():
    r = R.verify_proof("", H, "by omega")
    assert r.accepted and set(r.axioms) <= {"propext", "Quot.sound", "Classical.choice"}


@pytest.mark.parametrize("cand", ["by sorry", "by native_decide", "by omega\ntheorem x : False := sorry",
                                  "by\n  omega\n#print axioms foo", "by simp"])
def test_rejects_cheating_or_wrong(cand):
    assert not R.verify_proof("", H, cand).accepted


def test_sorry_in_whole_file_is_not_success():
    assert not R.check_source("theorem a : 1 = 2 := by sorry").accepted


def test_templates_are_machine_verified():
    from blindmath.theorem.verify_templates import verify
    total, bad = verify(n=60, seed=7)
    assert total == 60 and not bad, bad
