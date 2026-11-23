-- verified by Lean 4 (strict acceptance). source=baseline_tactics novelty=rediscovery
-- axioms: ['propext', 'Quot.sound']
def F (n : Nat) : Nat := if n % 2 = 0 then n / 2 else 3 * n + 1

def iter (f : Nat → Nat) : Nat → Nat → Nat
  | 0, n => n
  | k+1, n => iter f k (f n)

theorem F_odd_even (n : Nat) (h : n % 2 = 1) : F n % 2 = 0 := by unfold F; split <;> omega
