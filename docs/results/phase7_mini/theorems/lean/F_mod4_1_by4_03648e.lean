-- verified by Lean 4 (strict acceptance). source=baseline_tactics novelty=unclassified
-- axioms: ['propext', 'Quot.sound']
def F (n : Nat) : Nat := if n % 2 = 0 then n / 2 else 3 * n + 1

def iter (f : Nat → Nat) : Nat → Nat → Nat
  | 0, n => n
  | k+1, n => iter f k (f n)

theorem F_mod4_1_by4 (n : Nat) (h : n % 4 = 1) : F n % 4 = 0 := by unfold F; split <;> omega
