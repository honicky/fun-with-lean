/-
  Quicksort on lists of integers, with a proof that the result is always sorted.

  We define a purely functional quicksort using List.filter, then prove:
    `qsort_sorted : ∀ l, List.Pairwise (· ≤ ·) (qsort l)`
-/
import Mathlib.Data.List.Sort
import Mathlib.Tactic

/-! ## Definition -/

/-- Functional quicksort: pick the head as pivot, partition via filter. -/
def qsort : List Int → List Int
  | [] => []
  | x :: xs =>
    let lo := xs.filter (fun y => decide (y < x))
    let hi := xs.filter (fun y => decide (x ≤ y))
    qsort lo ++ [x] ++ qsort hi
termination_by l => l.length
decreasing_by
  all_goals simp_all
  all_goals (
    calc (List.filter _ xs.attach).length
        ≤ xs.attach.length := List.length_filter_le _ _
      _ = xs.length := List.length_attach)

@[simp] theorem qsort_nil : qsort [] = [] := by simp [qsort]

theorem qsort_cons (x : Int) (xs : List Int) :
    qsort (x :: xs) = qsort (xs.filter (fun y => decide (y < x))) ++ [x] ++
      qsort (xs.filter (fun y => decide (x ≤ y))) := by
  simp [qsort]

/-! ## Membership preservation -/

/-- If `a ∈ qsort l` then `a ∈ l`: quicksort does not introduce new elements. -/
theorem mem_qsort {a : Int} (l : List Int) (h : a ∈ qsort l) : a ∈ l := by
  match l with
  | [] => simp [qsort_nil] at h
  | x :: xs =>
    rw [qsort_cons] at h
    by_cases hlo : a ∈ qsort (xs.filter (fun y => decide (y < x)))
    · have := mem_qsort _ hlo
      simp [List.mem_filter] at this
      exact List.mem_cons_of_mem _ this.1
    · by_cases hmid : a = x
      · subst hmid; exact List.Mem.head ..
      · have hhi : a ∈ qsort (xs.filter (fun y => decide (x ≤ y))) := by
          simp only [List.mem_append, List.mem_cons] at h; tauto
        have := mem_qsort _ hhi
        simp [List.mem_filter] at this
        exact List.mem_cons_of_mem _ this.1
termination_by l.length
decreasing_by all_goals simp_all; exact List.length_filter_le _ _

/-! ## Bound lemmas -/

/-- Every element of `qsort (filter (· < x) xs)` is strictly less than `x`. -/
theorem qsort_lo_lt {xs : List Int} {x a : Int}
    (h : a ∈ qsort (xs.filter (fun y => decide (y < x)))) : a < x := by
  have h1 := mem_qsort _ h; simp [List.mem_filter] at h1; exact h1.2

/-- Every element of `qsort (filter (x ≤ ·) xs)` is at least `x`. -/
theorem qsort_hi_le {xs : List Int} {x a : Int}
    (h : a ∈ qsort (xs.filter (fun y => decide (x ≤ y)))) : x ≤ a := by
  have h1 := mem_qsort _ h; simp [List.mem_filter] at h1; exact h1.2

/-! ## Sorted helper -/

/-- Concatenating a sorted `lo`, a singleton `[x]`, and a sorted `hi` yields a sorted
    list, provided every element of `lo` is `≤ x` and every element of `hi` is `≥ x`. -/
theorem pairwise_lo_pivot_hi
    {lo : List Int} {x : Int} {hi : List Int}
    (hlo : List.Pairwise (· ≤ ·) lo)
    (hhi : List.Pairwise (· ≤ ·) hi)
    (hlo_le : ∀ a ∈ lo, a ≤ x)
    (hhi_le : ∀ a ∈ hi, x ≤ a) :
    List.Pairwise (· ≤ ·) (lo ++ [x] ++ hi) := by
  rw [List.pairwise_append]
  refine ⟨?_, ?_, ?_⟩
  · rw [List.pairwise_append]
    refine ⟨hlo, ?_, ?_⟩
    · simp [List.pairwise_cons]
    · intro a ha b hb
      simp only [List.mem_cons, List.mem_nil_iff] at hb
      obtain rfl | hf := hb
      · exact hlo_le a ha
      · simp at hf
  · exact hhi
  · intro a ha b hb
    simp only [List.mem_append, List.mem_cons, List.mem_nil_iff] at ha
    obtain ha_lo | rfl | hf := ha
    · exact le_trans (hlo_le a ha_lo) (hhi_le b hb)
    · exact hhi_le b hb
    · simp at hf

/-! ## Main theorem -/

/-- **Main theorem**: `qsort` always produces a sorted list — that is, the output
    satisfies `List.Pairwise (· ≤ ·)` for every input. -/
theorem qsort_sorted (l : List Int) : List.Pairwise (· ≤ ·) (qsort l) := by
  match l with
  | [] => simp [qsort_nil]
  | x :: xs =>
    rw [qsort_cons]
    apply pairwise_lo_pivot_hi
    · exact qsort_sorted (xs.filter (fun y => decide (y < x)))
    · exact qsort_sorted (xs.filter (fun y => decide (x ≤ y)))
    · intro a ha; exact le_of_lt (qsort_lo_lt ha)
    · intro a ha; exact qsort_hi_le ha
termination_by l.length
decreasing_by all_goals simp_all; exact List.length_filter_le _ _
