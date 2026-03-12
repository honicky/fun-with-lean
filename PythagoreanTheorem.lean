/-
  Formalization of the Pythagorean Theorem in Lean 4 with Mathlib

  We prove two versions:
  1. The inner product space version: if ⟨x, y⟩ = 0 then ‖x + y‖² = ‖x‖² + ‖y‖²
  2. The converse and the generalized version for finite orthogonal systems
-/
import Mathlib

open InnerProductSpace RealInnerProductSpace

noncomputable section

/-! ## Abstract Pythagorean Theorem in Inner Product Spaces -/

/-- **Pythagorean Theorem (inner product space version):**
    If x and y are orthogonal (⟨x, y⟩ = 0), then ‖x + y‖² = ‖x‖² + ‖y‖². -/
theorem pythagorean_theorem
    {E : Type*} [SeminormedAddCommGroup E] [InnerProductSpace ℝ E]
    (x y : E) (h_ortho : ⟪x, y⟫_ℝ = 0) :
    ‖x + y‖ ^ 2 = ‖x‖ ^ 2 + ‖y‖ ^ 2 := by
  rw [norm_add_sq_real]
  simp [h_ortho]

/-- **Converse of the Pythagorean Theorem:**
    If ‖x + y‖² = ‖x‖² + ‖y‖² then ⟨x, y⟩ = 0. -/
theorem pythagorean_converse
    {E : Type*} [SeminormedAddCommGroup E] [InnerProductSpace ℝ E]
    (x y : E) (h : ‖x + y‖ ^ 2 = ‖x‖ ^ 2 + ‖y‖ ^ 2) :
    ⟪x, y⟫_ℝ = 0 := by
  have := norm_add_sq_real x y
  linarith

/-- Pythagorean theorem for subtraction: ‖x - y‖² = ‖x‖² + ‖y‖² when orthogonal. -/
theorem pythagorean_sub
    {E : Type*} [SeminormedAddCommGroup E] [InnerProductSpace ℝ E]
    (x y : E) (h_ortho : ⟪x, y⟫_ℝ = 0) :
    ‖x - y‖ ^ 2 = ‖x‖ ^ 2 + ‖y‖ ^ 2 := by
  rw [norm_sub_sq_real]
  simp [h_ortho]

/-- **Pythagorean Theorem (iff version):**
    ‖x + y‖² = ‖x‖² + ‖y‖² if and only if x ⊥ y. -/
theorem pythagorean_iff
    {E : Type*} [SeminormedAddCommGroup E] [InnerProductSpace ℝ E]
    (x y : E) :
    ‖x + y‖ ^ 2 = ‖x‖ ^ 2 + ‖y‖ ^ 2 ↔ ⟪x, y⟫_ℝ = 0 :=
  ⟨pythagorean_converse x y, pythagorean_theorem x y⟩

/-! ## Generalized Pythagorean Theorem -/

/-- **Generalized Pythagorean theorem:** for pairwise orthogonal vectors,
    ‖∑ vᵢ‖² = ∑ ‖vᵢ‖². -/
theorem pythagorean_finset
    {E : Type*} [SeminormedAddCommGroup E] [InnerProductSpace ℝ E]
    {ι : Type*} [DecidableEq ι] (s : Finset ι) (v : ι → E)
    (h_ortho : ∀ i ∈ s, ∀ j ∈ s, i ≠ j → ⟪v i, v j⟫_ℝ = 0) :
    ‖s.sum v‖ ^ 2 = s.sum (fun i => ‖v i‖ ^ 2) := by
  induction s using Finset.cons_induction with
  | empty => simp
  | cons a s ha ih =>
    rw [Finset.sum_cons, Finset.sum_cons]
    have h_ortho_sub : ∀ i ∈ s, ∀ j ∈ s, i ≠ j → ⟪v i, v j⟫_ℝ = 0 := by
      intro i hi j hj hij
      exact h_ortho i (Finset.mem_cons.mpr (Or.inr hi)) j (Finset.mem_cons.mpr (Or.inr hj)) hij
    rw [norm_add_sq_real]
    have h_inner_zero : ⟪v a, s.sum v⟫_ℝ = 0 := by
      rw [inner_sum s v (v a)]
      apply Finset.sum_eq_zero
      intro i hi
      exact h_ortho a (Finset.mem_cons_self a s) i (Finset.mem_cons.mpr (Or.inr hi))
        (fun h => ha (h ▸ hi))
    simp [h_inner_zero, ih h_ortho_sub]

/-! ## Concrete ℝ² Application -/

/-- Application to ℝ²: vectors (a, 0) and (0, b) are orthogonal,
    so ‖(a, 0) + (0, b)‖² = ‖(a, 0)‖² + ‖(0, b)‖² = a² + b².
    This is the classical a² + b² = c² for a right triangle. -/
theorem pythagorean_R2 :
    ∀ (a b : EuclideanSpace ℝ (Fin 2)),
    ⟪a, b⟫_ℝ = 0 → ‖a + b‖ ^ 2 = ‖a‖ ^ 2 + ‖b‖ ^ 2 :=
  fun a b h => pythagorean_theorem a b h

/-- The law of cosines generalizes the Pythagorean theorem:
    ‖x + y‖² = ‖x‖² + ‖y‖² + 2⟨x, y⟩. -/
theorem law_of_cosines
    {E : Type*} [SeminormedAddCommGroup E] [InnerProductSpace ℝ E]
    (x y : E) :
    ‖x + y‖ ^ 2 = ‖x‖ ^ 2 + ‖y‖ ^ 2 + 2 * ⟪x, y⟫_ℝ := by
  rw [norm_add_sq_real]
  ring

end
