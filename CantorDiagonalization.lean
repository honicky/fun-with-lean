/-
  Formalization of Cantor's Diagonalization Theorem in Lean 4 with Mathlib

  We prove:
  1. No surjection from any set to its power set (Cantor's theorem)
  2. The reals are uncountable
  3. ℝ has strictly greater cardinality than ℕ
-/
import Mathlib

open Set Function Cardinal

noncomputable section

/-! ## Cantor's Theorem: No Surjection to Power Set -/

/-- **Cantor's Theorem:** There is no surjection from a set α to its power set.
    Proof by explicit diagonal construction. -/
theorem cantor_no_surjection (α : Type*) (f : α → Set α) : ¬ Surjective f := by
  intro h_surj
  set D : Set α := { x | x ∉ f x } with hD_def
  obtain ⟨d, hd⟩ := h_surj D
  have : d ∈ D ↔ d ∉ D := by
    constructor
    · intro h; rw [hD_def, Set.mem_setOf_eq] at h; rwa [hd] at h
    · intro h; rw [hD_def, Set.mem_setOf_eq]; rwa [hd]
  tauto

/-- Cantor's theorem (Mathlib version). -/
theorem cantor_no_surjection' (α : Type*) (f : α → Set α) : ¬ Surjective f :=
  Function.cantor_surjective f

/-- **Cantor's Theorem (injection form):**
    There is no injection from the power set of α into α. -/
theorem cantor_no_injection (α : Type*) (f : Set α → α) : ¬ Injective f :=
  Function.cantor_injective f

/-! ## Cardinality Results -/

/-- The cardinality of ℝ equals the continuum 2^ℵ₀. -/
theorem card_real_eq_continuum : #ℝ = continuum :=
  Cardinal.mk_real

/-- ℵ₀ < 2^ℵ₀. -/
theorem aleph0_lt_continuum' : ℵ₀ < continuum :=
  Cardinal.aleph0_lt_continuum

/-- ℕ has strictly smaller cardinality than ℝ. -/
theorem card_nat_lt_real : #ℕ < #ℝ := by
  rw [Cardinal.mk_real, Cardinal.mk_nat]
  exact Cardinal.aleph0_lt_continuum

/-! ## Uncountability of ℝ -/

/-- The reals are uncountable: there is no surjection from ℕ to ℝ. -/
theorem reals_uncountable : ¬ ∃ f : ℕ → ℝ, Surjective f := by
  intro ⟨f, hf⟩
  have h1 : #ℝ ≤ #ℕ := Cardinal.mk_le_of_surjective hf
  exact absurd (card_nat_lt_real.trans_le (le_refl _)) (not_lt.mpr h1)

/-- There is no bijection between ℕ and ℝ. -/
theorem no_bijection_nat_real : IsEmpty (ℕ ≃ ℝ) := by
  constructor
  intro e
  have : #ℕ = #ℝ := Cardinal.mk_congr e
  exact absurd card_nat_lt_real (not_lt.mpr this.symm.le)

/-! ## Diagonal Argument for Binary Sequences -/

/-- No function from ℕ to (ℕ → Bool) is surjective. -/
theorem cantor_sequences : ¬ ∃ f : ℕ → (ℕ → Bool), Surjective f := by
  intro ⟨f, hf⟩
  have h := hf (fun n => !f n n)
  obtain ⟨k, hk⟩ := h
  have : f k k = !f k k := congr_fun hk k
  simp at this

/-- The power set of ℕ is uncountable. -/
theorem powerset_nat_uncountable : ℵ₀ < #(Set ℕ) := by
  have : #(Set ℕ) = 2 ^ ℵ₀ := by
    rw [Cardinal.mk_set, Cardinal.mk_nat]
  rw [this]
  exact Cardinal.cantor ℵ₀

end
