/-
  Quicksort on lists of integers, with a proof that the result is always sorted.

  We define a purely functional quicksort using List.filter with median-of-three
  pivot selection (matching the companion Rust implementation), then prove:
    `qsort_sorted : ∀ l, List.Pairwise (· ≤ ·) (qsort l)`
-/
import Mathlib.Data.List.Sort
import Mathlib.Tactic

/-! ## Helpers -/

/-- Median of three integers. -/
def median3 (a b c : Int) : Int :=
  if a ≤ b then
    if b ≤ c then b       -- a ≤ b ≤ c
    else if a ≤ c then c   -- a ≤ c < b
    else a                 -- c < a ≤ b
  else -- b < a
    if a ≤ c then a        -- b < a ≤ c
    else if b ≤ c then c   -- b ≤ c < a
    else b                 -- c < b < a

/-- `median3 a b c` is always one of `a`, `b`, or `c`. -/
theorem median3_mem (a b c : Int) :
    median3 a b c = a ∨ median3 a b c = b ∨ median3 a b c = c := by
  simp only [median3]
  split <;> split <;> try (split <;> simp)
  all_goals simp

/-- Choose a pivot from a non-empty list using median-of-three.
    For short lists (length ≤ 2) just pick the head.
    Otherwise pick the median of the first, middle, and last elements. -/
def choosePivot (x : Int) (xs : List Int) : Int :=
  if h : xs.length < 2 then x
  else
    let last := xs.getLast (by intro h'; simp [h'] at h)
    let mid := (x :: xs)[((xs.length + 1) / 2)]'(by simp; omega)
    median3 x mid last

/-- The chosen pivot is always a member of the original list `x :: xs`. -/
theorem choosePivot_mem (x : Int) (xs : List Int) :
    choosePivot x xs ∈ x :: xs := by
  simp only [choosePivot]
  split
  · exact List.Mem.head ..
  · rename_i h
    have hmed := median3_mem x
      ((x :: xs)[((xs.length + 1) / 2)]'(by simp; omega))
      (xs.getLast (by intro h'; simp [h'] at h))
    rcases hmed with h1 | h1 | h1 <;> rw [h1]
    · exact List.Mem.head ..
    · exact List.getElem_mem ..
    · exact List.mem_cons_of_mem _ (List.getLast_mem ..)

/-- Remove one occurrence of `v` from a list. -/
def List.eraseVal (v : Int) : List Int → List Int
  | [] => []
  | x :: xs => if x == v then xs else x :: List.eraseVal v xs

/-- `eraseVal` on a list containing `v` reduces the length by one. -/
theorem List.length_eraseVal_of_mem {v : Int} {l : List Int} (h : v ∈ l) :
    (List.eraseVal v l).length = l.length - 1 := by
  induction l with
  | nil => simp at h
  | cons x xs ih =>
    simp only [eraseVal]
    split
    · simp
    · rename_i hne
      simp only [List.mem_cons] at h
      have hne' : v ≠ x := by
        intro heq; apply hne; rw [beq_iff_eq]; exact heq.symm
      rcases h with rfl | hmem
      · exact absurd rfl hne'
      · simp only [List.length_cons]; rw [ih hmem]
        have : xs.length ≥ 1 := by
          have := List.ne_nil_of_mem hmem
          cases xs with | nil => contradiction | cons _ _ => simp
        omega

/-- `eraseVal` produces a sublist: every element is from the original. -/
theorem List.mem_of_mem_eraseVal {a v : Int} {l : List Int}
    (h : a ∈ List.eraseVal v l) : a ∈ l := by
  induction l with
  | nil => simp [eraseVal] at h
  | cons x xs ih =>
    simp only [eraseVal] at h
    split at h
    · exact List.mem_cons_of_mem _ h
    · simp only [List.mem_cons] at h ⊢
      rcases h with rfl | h
      · left; rfl
      · right; exact ih h

/-! ## Definition -/

/-- Functional quicksort: choose median-of-three pivot, partition via filter. -/
def qsort : List Int → List Int
  | [] => []
  | x :: xs =>
    let pivot := choosePivot x xs
    let rest := List.eraseVal pivot (x :: xs)
    let lo := rest.filter (fun y => decide (y ≤ pivot))
    let hi := rest.filter (fun y => decide (pivot < y))
    qsort lo ++ [pivot] ++ qsort hi
termination_by l => l.length
decreasing_by
  all_goals simp_all
  all_goals (
    have hpiv := choosePivot_mem x xs
    have hlen := List.length_eraseVal_of_mem hpiv
    calc (List.filter _ (List.eraseVal (choosePivot x xs) (x :: xs))).length
        ≤ (List.eraseVal (choosePivot x xs) (x :: xs)).length :=
          List.length_filter_le _ _
      _ = (x :: xs).length - 1 := hlen
      _ = xs.length := by simp)

@[simp] theorem qsort_nil : qsort [] = [] := by simp [qsort]

theorem qsort_cons (x : Int) (xs : List Int) :
    qsort (x :: xs) =
      let pivot := choosePivot x xs
      let rest := List.eraseVal pivot (x :: xs)
      let lo := rest.filter (fun y => decide (y ≤ pivot))
      let hi := rest.filter (fun y => decide (pivot < y))
      qsort lo ++ [pivot] ++ qsort hi := by
  simp [qsort]

/-! ## Membership preservation -/

/-- If `a ∈ qsort l` then `a ∈ l`: quicksort does not introduce new elements. -/
theorem mem_qsort {a : Int} (l : List Int) (h : a ∈ qsort l) : a ∈ l := by
  match l with
  | [] => simp [qsort_nil] at h
  | x :: xs =>
    simp only [qsort] at h
    have hpiv := choosePivot_mem x xs
    by_cases hlo : a ∈ qsort ((List.eraseVal (choosePivot x xs) (x :: xs)).filter
        (fun y => decide (y ≤ choosePivot x xs)))
    · have hmem := mem_qsort _ hlo
      simp only [List.mem_filter, decide_eq_true_eq] at hmem
      exact List.mem_of_mem_eraseVal hmem.1
    · by_cases hmid : a = choosePivot x xs
      · rw [hmid]; exact hpiv
      · have hhi : a ∈ qsort ((List.eraseVal (choosePivot x xs) (x :: xs)).filter
            (fun y => decide (choosePivot x xs < y))) := by
          simp only [List.mem_append, List.mem_cons] at h; tauto
        have hmem := mem_qsort _ hhi
        simp only [List.mem_filter, decide_eq_true_eq] at hmem
        exact List.mem_of_mem_eraseVal hmem.1
termination_by l.length
decreasing_by
  all_goals simp_all
  all_goals (
    have hpiv := choosePivot_mem x xs
    have hlen := List.length_eraseVal_of_mem hpiv
    calc (List.filter _ (List.eraseVal (choosePivot x xs) (x :: xs))).length
        ≤ (List.eraseVal (choosePivot x xs) (x :: xs)).length :=
          List.length_filter_le _ _
      _ = (x :: xs).length - 1 := hlen
      _ = xs.length := by simp)

/-! ## Bound lemmas -/

/-- Every element of `qsort (filter (· ≤ pivot) rest)` is `≤ pivot`. -/
theorem qsort_lo_le {rest : List Int} {pivot a : Int}
    (h : a ∈ qsort (rest.filter (fun y => decide (y ≤ pivot)))) : a ≤ pivot := by
  have hmem := mem_qsort _ h
  simp only [List.mem_filter, decide_eq_true_eq] at hmem
  exact hmem.2

/-- Every element of `qsort (filter (pivot < ·) rest)` is `> pivot`. -/
theorem qsort_hi_gt {rest : List Int} {pivot a : Int}
    (h : a ∈ qsort (rest.filter (fun y => decide (pivot < y)))) : pivot < a := by
  have hmem := mem_qsort _ h
  simp only [List.mem_filter, decide_eq_true_eq] at hmem
  exact hmem.2

/-! ## Sorted helper -/

/-- Concatenating a sorted `lo`, a singleton `[pivot]`, and a sorted `hi` yields
    a sorted list, provided every element of `lo` is `≤ pivot` and every element
    of `hi` is `> pivot` (hence `≥ pivot`). -/
theorem pairwise_lo_pivot_hi
    {lo : List Int} {pivot : Int} {hi : List Int}
    (hlo : List.Pairwise (· ≤ ·) lo)
    (hhi : List.Pairwise (· ≤ ·) hi)
    (hlo_le : ∀ a ∈ lo, a ≤ pivot)
    (hhi_gt : ∀ a ∈ hi, pivot < a) :
    List.Pairwise (· ≤ ·) (lo ++ [pivot] ++ hi) := by
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
    · exact le_trans (hlo_le a ha_lo) (le_of_lt (hhi_gt b hb))
    · exact le_of_lt (hhi_gt b hb)
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
    · exact qsort_sorted _
    · exact qsort_sorted _
    · intro a ha; exact qsort_lo_le ha
    · intro a ha; exact qsort_hi_gt ha
termination_by l.length
decreasing_by
  all_goals simp_all
  all_goals (
    have hlen := List.length_eraseVal_of_mem (choosePivot_mem x xs)
    calc (List.filter _ (List.eraseVal (choosePivot x xs) (x :: xs))).length
        ≤ (List.eraseVal (choosePivot x xs) (x :: xs)).length :=
          List.length_filter_le _ _
      _ = (x :: xs).length - 1 := hlen
      _ = xs.length := by simp)
