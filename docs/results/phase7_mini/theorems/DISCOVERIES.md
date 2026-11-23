# Discoveries

Lean-verified theorems: 37  |  conjectures logged: 30

## Verified theorems (strict Lean acceptance)

- `theorem F_even (n : Nat) (h : n % 2 = 0) : F n = n / 2 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: rediscovery
- `theorem F_odd (n : Nat) (h : n % 2 = 1) : F n = 3 * n + 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: rediscovery
- `theorem F_odd_even (n : Nat) (h : n % 2 = 1) : F n % 2 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: rediscovery
- `theorem F_lt_even (n : Nat) (h : n % 2 = 0) (h0 : 0 < n) : F n < n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: rediscovery
- `theorem F_pos (n : Nat) (h : 0 < n) : 0 < F n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: rediscovery
- `theorem F_double (n : Nat) : F (2 * n) = n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: rediscovery
- `theorem iter_add (f : Nat → Nat) (a b n : Nat) : iter f (a + b) n = iter f b (iter f a n) :=`  
  proof: `by` — source: baseline_tactics, novelty: rediscovery
- `theorem F_lt_mod2_0 (n : Nat) (h : n % 2 = 0) (h0 : 0 < n) : F n < n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod2_1_by2 (n : Nat) (h : n % 2 = 1) : F n % 2 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod2_1_by3 (n : Nat) (h : n % 2 = 1) : F n % 3 = 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_gt_mod2_1 (n : Nat) (h : n % 2 = 1) : n < F n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod3_2_by3 (n : Nat) (h : n % 3 = 2) : F n % 3 = 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod4_0_by2 (n : Nat) (h : n % 4 = 0) : F n % 2 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_lt_mod4_0 (n : Nat) (h : n % 4 = 0) (h0 : 0 < n) : F n < n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod4_1_by2 (n : Nat) (h : n % 4 = 1) : F n % 2 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod4_1_by3 (n : Nat) (h : n % 4 = 1) : F n % 3 = 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod4_1_by4 (n : Nat) (h : n % 4 = 1) : F n % 4 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_gt_mod4_1 (n : Nat) (h : n % 4 = 1) : n < F n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod4_2_by2 (n : Nat) (h : n % 4 = 2) : F n % 2 = 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_lt_mod4_2 (n : Nat) (h : n % 4 = 2) (h0 : 0 < n) : F n < n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod4_3_by2 (n : Nat) (h : n % 4 = 3) : F n % 2 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod4_3_by3 (n : Nat) (h : n % 4 = 3) : F n % 3 = 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod4_3_by4 (n : Nat) (h : n % 4 = 3) : F n % 4 = 2 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_gt_mod4_3 (n : Nat) (h : n % 4 = 3) : n < F n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod6_0_by3 (n : Nat) (h : n % 6 = 0) : F n % 3 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_lt_mod6_0 (n : Nat) (h : n % 6 = 0) (h0 : 0 < n) : F n < n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod6_1_by2 (n : Nat) (h : n % 6 = 1) : F n % 2 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod6_1_by3 (n : Nat) (h : n % 6 = 1) : F n % 3 = 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_gt_mod6_1 (n : Nat) (h : n % 6 = 1) : n < F n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod6_2_by3 (n : Nat) (h : n % 6 = 2) : F n % 3 = 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_lt_mod6_2 (n : Nat) (h : n % 6 = 2) (h0 : 0 < n) : F n < n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod6_3_by2 (n : Nat) (h : n % 6 = 3) : F n % 2 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod6_3_by3 (n : Nat) (h : n % 6 = 3) : F n % 3 = 1 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_gt_mod6_3 (n : Nat) (h : n % 6 = 3) : n < F n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod6_4_by3 (n : Nat) (h : n % 6 = 4) : F n % 3 = 2 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_lt_mod6_4 (n : Nat) (h : n % 6 = 4) (h0 : 0 < n) : F n < n :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified
- `theorem F_mod6_5_by2 (n : Nat) (h : n % 6 = 5) : F n % 2 = 0 :=`  
  proof: `by unfold F; split <;> omega` — source: baseline_tactics, novelty: unclassified

## Conjectures (NOT theorems unless status=proved)

- [proved] if n = 0 mod 2 (n>0) then F(n) < n
- [proved] if n = 1 mod 2 then F(n) = 0 mod 2
- [proved] if n = 1 mod 2 then F(n) = 1 mod 3
- [proved] if n = 1 mod 2 then F(n) > n
- [proved] if n = 2 mod 3 then F(n) = 1 mod 3
- [proved] if n = 0 mod 4 then F(n) = 0 mod 2
- [proved] if n = 0 mod 4 (n>0) then F(n) < n
- [proved] if n = 1 mod 4 then F(n) = 0 mod 2
- [proved] if n = 1 mod 4 then F(n) = 1 mod 3
- [proved] if n = 1 mod 4 then F(n) = 0 mod 4
- [proved] if n = 1 mod 4 then F(n) > n
- [proved] if n = 2 mod 4 then F(n) = 1 mod 2
- [proved] if n = 2 mod 4 (n>0) then F(n) < n
- [proved] if n = 3 mod 4 then F(n) = 0 mod 2
- [proved] if n = 3 mod 4 then F(n) = 1 mod 3
- [proved] if n = 3 mod 4 then F(n) = 2 mod 4
- [proved] if n = 3 mod 4 then F(n) > n
- [proved] if n = 0 mod 6 then F(n) = 0 mod 3
- [proved] if n = 0 mod 6 (n>0) then F(n) < n
- [proved] if n = 1 mod 6 then F(n) = 0 mod 2
- [proved] if n = 1 mod 6 then F(n) = 1 mod 3
- [proved] if n = 1 mod 6 then F(n) > n
- [proved] if n = 2 mod 6 then F(n) = 1 mod 3
- [proved] if n = 2 mod 6 (n>0) then F(n) < n
- [proved] if n = 3 mod 6 then F(n) = 0 mod 2
- [proved] if n = 3 mod 6 then F(n) = 1 mod 3
- [proved] if n = 3 mod 6 then F(n) > n
- [proved] if n = 4 mod 6 then F(n) = 2 mod 3
- [proved] if n = 4 mod 6 (n>0) then F(n) < n
- [proved] if n = 5 mod 6 then F(n) = 0 mod 2
