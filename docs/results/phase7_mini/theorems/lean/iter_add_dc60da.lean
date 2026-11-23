-- verified by Lean 4 (strict acceptance). source=baseline_tactics novelty=rediscovery
-- axioms: ['propext', 'Quot.sound']
def iter (f : Nat → Nat) : Nat → Nat → Nat
  | 0, n => n
  | k+1, n => iter f k (f n)

theorem iter_add (f : Nat → Nat) (a b n : Nat) : iter f (a + b) n = iter f b (iter f a n) := by
  induction a generalizing n with
  | zero => simp [iter]
  | succ k ih =>
    rw [show k + 1 + b = (k + b) + 1 by omega]
    simp only [iter]
    exact ih (f n)
