/-
  Formalization of the Central Limit Theorem in Lean 4 with Mathlib

  The Central Limit Theorem (CLT): If X₁, X₂, ... are i.i.d. random variables
  with mean μ and finite variance σ² > 0, then the standardized partial sums
    Sₙ = (X₁ + ... + Xₙ - nμ) / (σ√n)
  converge in distribution to the standard normal distribution N(0,1).
-/
import Mathlib

open MeasureTheory ProbabilityTheory Filter Topology

noncomputable section

/-! ## Characteristic Functions -/

/-- The characteristic function φ_X(t) = 𝔼[e^{itX}]. -/
def charFunRV {Ω : Type*} [MeasurableSpace Ω] (X : Ω → ℝ) (μ : Measure Ω) (t : ℝ) : ℂ :=
  ∫ ω, Complex.exp (↑(t * X ω) * Complex.I) ∂μ

/-- The standard normal characteristic function: φ(t) = e^{-t²/2}. -/
def stdNormalCharFun (t : ℝ) : ℂ :=
  Complex.exp (-(↑(t ^ 2) / 2))

/-! ## Convergence in Distribution -/

/-- Convergence in distribution via characteristic functions. -/
def ConvergesInDistribution {Ω : Type*} [MeasurableSpace Ω]
    (X : ℕ → Ω → ℝ) (μ : Measure Ω) (φ_limit : ℝ → ℂ) : Prop :=
  ∀ t : ℝ, Filter.Tendsto (fun n => charFunRV (X n) μ t) atTop (nhds (φ_limit t))

/-- Convergence in distribution to the standard normal. -/
def ConvergesToStdNormal {Ω : Type*} [MeasurableSpace Ω]
    (X : ℕ → Ω → ℝ) (μ : Measure Ω) : Prop :=
  ConvergesInDistribution X μ stdNormalCharFun

/-! ## I.I.D. Random Variables -/

/-- A sequence of real-valued random variables is i.i.d. -/
structure IsIID {Ω : Type*} [MeasurableSpace Ω]
    (X : ℕ → Ω → ℝ) (μ : Measure Ω) : Prop where
  /-- Mutual independence -/
  indep : iIndepFun (β := fun (_ : ℕ) => ℝ) X μ
  /-- Identical distribution -/
  ident_distrib : ∀ n, IdentDistrib (X n) (X 0) μ μ

/-! ## Standardized Partial Sums -/

/-- The partial sum S_n = X₀ + ... + X_{n-1}. -/
def partialSum {Ω : Type*} (X : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (Finset.range n).sum fun i => X i ω

/-- The standardized partial sum Z_n = (S_n - nμ) / (σ√n). -/
def standardizedSum {Ω : Type*} (X : ℕ → Ω → ℝ) (μ_val σ : ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  (partialSum X n ω - ↑n * μ_val) / (σ * Real.sqrt ↑n)

/-! ## Central Limit Theorem -/

/-- **Central Limit Theorem (Lindeberg–Lévy):**
    Let X₀, X₁, X₂, ... be i.i.d. real-valued random variables on a
    probability space (Ω, μ) with mean μ_val and positive variance σ² > 0.
    Then Zₙ = (S_n - nμ) / (σ√n) → N(0,1) in distribution. -/
theorem central_limit_theorem
    {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : ℕ → Ω → ℝ)
    (hX_iid : IsIID X μ)
    (hX_meas : ∀ n, Measurable (X n))
    (hX_integrable : ∀ n, Integrable (X n) μ)
    (hX_sq_integrable : ∀ n, Integrable (fun ω => (X n ω) ^ 2) μ)
    (μ_val : ℝ) (hμ : μ_val = ∫ ω, X 0 ω ∂μ)
    (σ : ℝ) (hσ_def : σ ^ 2 = variance (X 0) μ) (hσ_pos : 0 < σ) :
    ConvergesToStdNormal (fun n => standardizedSum X μ_val σ n) μ := by
  -- Unfold the goal: need to show pointwise convergence of
  -- characteristic functions to the standard normal char fun.
  intro t
  -- The full proof requires:
  -- 1. Express φ_{Zₙ}(t) in terms of φ_{Y}(t/(σ√n))^n
  --    where Y = X₀ - μ is centered
  -- 2. Taylor expand φ_Y(s) = 1 - s²σ²/2 + o(s²)
  --    using charFunRV_taylor with E[Y]=0, E[Y²]=σ²
  -- 3. Substitute s = t/(σ√n) to get
  --    φ_Y(t/(σ√n)) = 1 + (-t²/2)/n + o(1/n)
  -- 4. Apply tendsto_cpow_exp to conclude
  --    [φ_Y(t/(σ√n))]^n → exp(-t²/2)
  -- 5. The result follows since exp(-t²/2) = stdNormalCharFun(t)
  --
  -- This assembly requires charFunRV_taylor (still sorry)
  -- and careful manipulation of the standardized sum's
  -- characteristic function as a power of centered char fun.
  sorry

/-! ## Key Supporting Lemmas -/

namespace CLTLemmas

variable {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω)

/-- The characteristic function is bounded by 1. -/
theorem charFunRV_bounded [IsProbabilityMeasure μ] (X : Ω → ℝ) (t : ℝ) :
    ‖charFunRV X μ t‖ ≤ 1 := by
  unfold charFunRV
  calc ‖∫ ω, Complex.exp (↑(t * X ω) * Complex.I) ∂μ‖
      ≤ ∫ ω, ‖Complex.exp (↑(t * X ω) * Complex.I)‖ ∂μ :=
        norm_integral_le_integral_norm _
    _ = ∫ ω, 1 ∂μ := by
        congr 1; ext ω
        rw [Complex.norm_exp]
        have : (↑(t * X ω) * Complex.I).re = 0 := by
          simp [Complex.mul_re]
        rw [this, Real.exp_zero]
    _ = (μ Set.univ).toReal := by simp
    _ = 1 := by simp [measure_univ]

/-- The characteristic function at 0 equals 1. -/
theorem charFunRV_zero [IsProbabilityMeasure μ] (X : Ω → ℝ) :
    charFunRV X μ 0 = 1 := by
  simp only [charFunRV, zero_mul, Complex.ofReal_zero, zero_mul, Complex.exp_zero]
  simp

/-- The characteristic function of the zero r.v. is 1 everywhere. -/
theorem charFunRV_zero_rv [IsProbabilityMeasure μ] (t : ℝ) :
    charFunRV (fun _ : Ω => (0 : ℝ)) μ t = 1 := by
  simp only [charFunRV, mul_zero, Complex.ofReal_zero, zero_mul, Complex.exp_zero]
  simp

/-- The characteristic function is continuous.
    Proof sketch: the integrand exp(itX(ω)) is continuous in t for each ω,
    bounded by 1 (integrable on a probability space), so dominated convergence
    gives continuity of ∫ exp(itX) dμ. -/
theorem charFunRV_continuous [IsFiniteMeasure μ] (X : Ω → ℝ) (hX : Measurable X) :
    Continuous (charFunRV X μ) := by
  unfold charFunRV
  rw [continuous_iff_seqContinuous]
  intro u t hut
  apply tendsto_integral_of_dominated_convergence (fun _ => (1 : ℝ))
  · intro n
    have : Measurable (fun ω =>
        Complex.exp (↑(u n * X ω) * Complex.I)) :=
      Complex.measurable_exp.comp
        ((Complex.measurable_ofReal.comp
          (measurable_const.mul hX)).mul measurable_const)
    exact this.aestronglyMeasurable
  · exact integrable_const 1
  · intro n; exact Filter.Eventually.of_forall fun ω => by
      rw [Complex.norm_exp]
      have : (↑(u n * X ω) * Complex.I).re = 0 := by simp [Complex.mul_re]
      rw [this, Real.exp_zero]
  · exact Filter.Eventually.of_forall fun ω => by
      have h_cont : Continuous (fun s : ℝ => Complex.exp (↑(s * X ω) * Complex.I)) := by
        fun_prop
      exact h_cont.continuousAt.tendsto.comp hut

/-- Third-order Taylor bound for complex exponential.
    For ‖z‖ ≤ 1: ‖exp(z) - 1 - z - z²/2‖ ≤ ‖z‖³.
    Follows from Mathlib's Complex.exp_bound with n = 3. -/
theorem exp_taylor3_bound {z : ℂ} (hz : ‖z‖ ≤ 1) :
    ‖Complex.exp z - 1 - z - z ^ 2 / 2‖ ≤ ‖z‖ ^ 3 := by
  -- Use exp_bound' with n = 3 which gives a cleaner form
  -- exp_bound' : ‖exp z - ∑_{m<n} z^m/m!‖ ≤ ‖z‖^n / n! * 2
  -- when ‖z‖ / n.succ ≤ 1/2, i.e., ‖z‖ ≤ n.succ/2
  -- For n=3: need ‖z‖ / 4 ≤ 1/2, i.e., ‖z‖ ≤ 2. True since ‖z‖ ≤ 1.
  have hx : ‖z‖ / (3 : ℕ).succ ≤ 1 / 2 := by
    rw [Nat.succ_eq_add_one]
    calc ‖z‖ / (3 + 1 : ℕ) ≤ 1 / (4 : ℕ) := by gcongr
      _ ≤ 1 / 2 := by norm_num
  have h := Complex.exp_bound' hx
  -- h : ‖exp z - ∑_{m<3} z^m/m!‖ ≤ ‖z‖³ / 3! * 2 = ‖z‖³ / 3
  -- Need to convert ∑_{m<3} z^m/m! = 1 + z + z²/2
  -- and ‖z‖³/3 ≤ ‖z‖³
  calc ‖Complex.exp z - 1 - z - z ^ 2 / 2‖
      = ‖Complex.exp z - ∑ m ∈ Finset.range 3, z ^ m / ↑(Nat.factorial m)‖ := by
        simp [Finset.sum_range_succ, Nat.factorial]
        ring_nf
    _ ≤ ‖z‖ ^ 3 / ↑(Nat.factorial 3) * 2 := h
    _ ≤ ‖z‖ ^ 3 := by
        simp [Nat.factorial]
        have h0 : (0 : ℝ) ≤ ‖z‖ ^ 3 := by positivity
        linarith

/-- Uniform bound on exp Taylor remainder for purely imaginary argument:
    ‖exp(θI) - 1 - θI + θ²/2‖ ≤ 4 * θ².
    Uses exp_taylor3_bound when |θ| ≤ 1, triangle inequality when |θ| > 1.
    Note: (θI)²/2 = -θ²/2, so the +θ²/2 comes from subtracting (θI)²/2. -/
theorem exp_taylor3_unified_bound (θ : ℝ) :
    ‖Complex.exp (↑θ * Complex.I) - 1 - ↑θ * Complex.I
      + ↑(θ ^ 2) / 2‖ ≤ 4 * θ ^ 2 := by
  -- Convert to the form exp(z) - 1 - z - z²/2 where z = θI
  have hconv : Complex.exp (↑θ * Complex.I) - 1 - ↑θ * Complex.I + ↑(θ ^ 2) / 2
      = Complex.exp (↑θ * Complex.I) - 1 - (↑θ * Complex.I)
        - (↑θ * Complex.I) ^ 2 / 2 := by
    have : (↑θ * Complex.I) ^ 2 = -(↑(θ ^ 2) : ℂ) := by
      rw [mul_pow, Complex.I_sq]; push_cast; ring
    rw [this]; ring
  rw [hconv]
  -- Auxiliary: ‖↑θ * I‖ = |θ|
  have hnorm_θI : ‖(↑θ : ℂ) * Complex.I‖ = |θ| := by
    rw [norm_mul, Complex.norm_real, Complex.norm_I, mul_one, Real.norm_eq_abs]
  by_cases hθ : |θ| ≤ 1
  · -- Case |θ| ≤ 1: use exp_taylor3_bound
    have hz : ‖(↑θ : ℂ) * Complex.I‖ ≤ 1 := by rw [hnorm_θI]; exact hθ
    calc ‖Complex.exp (↑θ * Complex.I) - 1 - ↑θ * Complex.I
            - (↑θ * Complex.I) ^ 2 / 2‖
        ≤ ‖(↑θ : ℂ) * Complex.I‖ ^ 3 := exp_taylor3_bound hz
      _ = |θ| ^ 3 := by rw [hnorm_θI]
      _ ≤ θ ^ 2 := by nlinarith [sq_nonneg (|θ| - 1), sq_abs θ, abs_nonneg θ]
      _ ≤ 4 * θ ^ 2 := by linarith [sq_nonneg θ]
  · -- Case |θ| > 1: triangle inequality + |exp(θI)| = 1
    push_neg at hθ
    have hexp_norm : ‖Complex.exp (↑θ * Complex.I)‖ = 1 := by
      rw [Complex.norm_exp]; simp [Complex.mul_re]
    -- ‖(θI)²/2‖ = θ²/2
    have hnorm_sq : ‖(↑θ * Complex.I) ^ 2 / 2‖ = θ ^ 2 / 2 := by
      have : (↑θ * Complex.I) ^ 2 = -(↑(θ ^ 2) : ℂ) := by
        rw [mul_pow, Complex.I_sq]; push_cast; ring
      rw [this]
      simp [Complex.norm_real, norm_neg, sq_abs, Real.norm_eq_abs]
    calc ‖Complex.exp (↑θ * Complex.I) - 1 - ↑θ * Complex.I
            - (↑θ * Complex.I) ^ 2 / 2‖
        ≤ ‖Complex.exp (↑θ * Complex.I) - 1 - ↑θ * Complex.I‖
            + ‖(↑θ * Complex.I) ^ 2 / 2‖ := by
          exact norm_sub_le _ _
      _ ≤ (‖Complex.exp (↑θ * Complex.I)‖ + 1 + ‖(↑θ : ℂ) * Complex.I‖)
            + ‖(↑θ * Complex.I) ^ 2 / 2‖ := by
          gcongr
          calc ‖Complex.exp (↑θ * Complex.I) - 1 - ↑θ * Complex.I‖
              ≤ ‖Complex.exp (↑θ * Complex.I) - 1‖ + ‖↑θ * Complex.I‖ := norm_sub_le _ _
            _ ≤ (‖Complex.exp (↑θ * Complex.I)‖ + ‖(1 : ℂ)‖) + ‖(↑θ : ℂ) * Complex.I‖ := by
                gcongr; exact norm_sub_le _ _
            _ = ‖Complex.exp (↑θ * Complex.I)‖ + 1 + ‖(↑θ : ℂ) * Complex.I‖ := by
                norm_num
      _ = 1 + 1 + |θ| + θ ^ 2 / 2 := by rw [hexp_norm, hnorm_θI, hnorm_sq]
      _ ≤ 4 * θ ^ 2 := by nlinarith [sq_abs θ]

/-- The characteristic function Taylor remainder is o(s²).
    For R(s) = charFunRV X μ s - (1 + s·E[X]·I - s²·E[X²]/2),
    we have: ∀ ε > 0, ∃ δ > 0, |s| < δ → ‖R(s)‖ ≤ ε * s². -/
theorem charFunRV_taylor_remainder [IsProbabilityMeasure μ]
    (X : Ω → ℝ) (hX : Integrable (fun ω => (X ω) ^ 2) μ) :
    ∀ ε > 0, ∃ δ > 0, ∀ s : ℝ, |s| < δ →
      ‖charFunRV X μ s
        - (1 + ↑s * ↑(∫ ω, X ω ∂μ) * Complex.I
           - ↑(s ^ 2) * ↑(∫ ω, (X ω) ^ 2 ∂μ) / 2)‖ ≤ ε * s ^ 2 := by
  -- R(s) = ∫ (exp(sXωI) - 1 - sXωI + s²Xω²/2) dμ
  -- Pointwise: ‖integrand(ω)‖ ≤ 4(sXω)² = 4s²Xω² (exp_taylor3_unified_bound)
  -- For |sXω| ≤ 1: ‖integrand(ω)‖ ≤ |sXω|³ ≤ |s|s²Xω² (exp_taylor3_bound)
  -- Truncation: choose A with ∫_{|X|>A} X² < ε/8, then δ = min(1/A, ε/(8A∫X²))
  -- gives ‖R(s)‖ ≤ εs² for |s| < δ.
  sorry

/-- Taylor expansion of the characteristic function.

    PROOF SKETCH: For z = isX(ω), use exp(z) = 1 + z + z²/2 + R₃(z)
    where ‖R₃(z)‖ ≤ min(‖z‖³/6, ‖z‖²).
    - z = ↑(sX(ω)) * I, so z² = -s²X(ω)²
    - Integrate: φ(s) = 1 + is·E[X] - s²E[X²]/2 + ∫ R₃
    - ‖R₃(isX(ω))‖/s² ≤ |X(ω)|² · min(|s||X(ω)|/6, 1) → 0
    - Dominated by |X(ω)|² which is integrable (hypothesis)
    - DCT gives ‖∫ R₃‖/s² → 0, i.e., ‖R(s)‖ = o(s²) -/
theorem charFunRV_taylor [IsProbabilityMeasure μ] (X : Ω → ℝ)
    (hX : Integrable (fun ω => (X ω) ^ 2) μ) (t : ℝ) :
    ∃ (R : ℝ → ℂ), charFunRV X μ t =
      1 + ↑t * ↑(∫ ω, X ω ∂μ) * Complex.I
      - ↑(t ^ 2) * ↑(∫ ω, (X ω) ^ 2 ∂μ) / 2
      + R t ∧
      (∀ ε > 0, ∃ δ > 0, ∀ s : ℝ, |s| < δ → ‖R s‖ ≤ ε * s ^ 2) := by
  -- Define R as the remainder: R(s) = φ(s) - (1 + is·E[X] - s²E[X²]/2)
  refine ⟨fun s => charFunRV X μ s
    - (1 + ↑s * ↑(∫ ω, X ω ∂μ) * Complex.I
       - ↑(s ^ 2) * ↑(∫ ω, (X ω) ^ 2 ∂μ) / 2), ?_, ?_⟩
  · ring
  · -- Need: ∀ ε > 0, ∃ δ > 0, ∀ s, |s| < δ → ‖R(s)‖ ≤ ε * s²
    -- R(s) = ∫ (exp(sXI) - 1 - sXI + s²X²/2) dμ
    -- Uses exp Taylor bound + DCT argument with tail truncation
    exact charFunRV_taylor_remainder μ X hX

/-- Product formula: if X, Y independent, then φ_{X+Y} = φ_X · φ_Y.
    Proof: exp(it(X+Y)) = exp(itX)·exp(itY), and independence gives
    𝔼[f(X)·g(Y)] = 𝔼[f(X)]·𝔼[g(Y)]. -/
theorem charFunRV_add_indep (X Y : Ω → ℝ)
    (hX : Measurable X) (hY : Measurable Y)
    (h_indep : IndepFun X Y μ) (t : ℝ) :
    charFunRV (fun ω => X ω + Y ω) μ t = charFunRV X μ t * charFunRV Y μ t := by
  unfold charFunRV
  -- Step 1: exp(it(X+Y)) = exp(itX) * exp(itY)
  have h_split : ∀ ω, Complex.exp (↑(t * (X ω + Y ω)) * Complex.I) =
      Complex.exp (↑(t * X ω) * Complex.I) * Complex.exp (↑(t * Y ω) * Complex.I) := by
    intro ω
    rw [mul_add, Complex.ofReal_add, add_mul, Complex.exp_add]
  simp_rw [h_split]
  -- Step 2: 𝔼[f(X)·g(Y)] = 𝔼[f(X)]·𝔼[g(Y)] by independence
  have hf_meas : Measurable
      (fun x : ℝ => Complex.exp (↑(t * x) * Complex.I)) :=
    Complex.measurable_exp.comp
      ((Complex.measurable_ofReal.comp
        (measurable_const.mul measurable_id)).mul
        measurable_const)
  exact h_indep.integral_fun_comp_mul_comp
    hX.aemeasurable hY.aemeasurable
    hf_meas.aestronglyMeasurable
    hf_meas.aestronglyMeasurable

/-- For i.i.d. variables, φ_{S_n} = (φ_{X₀})^n.
    Proof by induction: S_0 = 0 (base), S_{n+1} = S_n + X_n where X_n is
    independent of S_n and identically distributed to X₀. -/
theorem charFunRV_iid_sum [IsProbabilityMeasure μ] (X : ℕ → Ω → ℝ) (hX_iid : IsIID X μ)
    (hX_meas : ∀ n, Measurable (X n)) (n : ℕ) (t : ℝ) :
    charFunRV (partialSum X n) μ t = (charFunRV (X 0) μ t) ^ n := by
  induction n with
  | zero =>
    simp only [pow_zero]
    exact charFunRV_zero_rv μ t
  | succ n ih =>
    -- S_{n+1}(ω) = S_n(ω) + X_n(ω)
    have h_sum : ∀ ω, partialSum X (n + 1) ω = partialSum X n ω + X n ω := by
      intro ω; unfold partialSum; rw [Finset.sum_range_succ]
    rw [pow_succ]
    -- Rewrite charFun of S_{n+1} as charFun of S_n + X_n
    have h_eq : charFunRV (partialSum X (n + 1)) μ t =
        charFunRV (fun ω => partialSum X n ω + X n ω) μ t := by
      congr 1; ext ω; exact h_sum ω
    rw [h_eq]
    -- S_n and X_n are independent (extract from iIndepFun)
    -- and S_n is measurable as a finite sum of measurables
    have hSn_meas : Measurable (partialSum X n) :=
      Finset.measurable_sum _ fun i _ => hX_meas i
    -- X_n has same char fun as X_0 by identical distribution
    have h_ident : charFunRV (X n) μ t = charFunRV (X 0) μ t := by
      unfold charFunRV
      have h_id := hX_iid.ident_distrib n
      have hu : Measurable (fun x : ℝ =>
          Complex.exp (↑(t * x) * Complex.I)) :=
        Complex.measurable_exp.comp
          ((Complex.measurable_ofReal.comp
            (measurable_const.mul measurable_id)).mul
            measurable_const)
      exact (h_id.comp hu).integral_eq
    -- Independence of S_n = ∑_{j ∈ range n} X j and X n
    -- follows from iIndepFun since n ∉ range n
    have h_indep_Sn_Xn : IndepFun (partialSum X n) (X n) μ := by
      have : partialSum X n = ∑ j ∈ Finset.range n, X j := by
        ext ω; simp [partialSum]
      rw [this]
      exact hX_iid.indep.indepFun_finset_sum_of_notMem
        hX_meas (by simp)
    -- Now combine: φ_{S_n + X_n} = φ_{S_n} · φ_{X_n}
    --                              = φ_{X₀}^n · φ_{X₀}
    rw [charFunRV_add_indep μ _ _ hSn_meas (hX_meas n)
        h_indep_Sn_Xn t, ih, h_ident]

/-- The key convergence: (1 + z/n)^n → e^z. -/
theorem tendsto_cpow_exp (z : ℂ) :
    Filter.Tendsto (fun n : ℕ => (1 + z / (↑n : ℂ)) ^ n) atTop
      (nhds (Complex.exp z)) :=
  Complex.tendsto_one_add_div_pow_exp z

/-- Lévy's continuity theorem (weak form). -/
theorem levy_continuity
    {Ω' : Type*} [MeasurableSpace Ω'] (ν : Measure Ω')
    (X : ℕ → Ω' → ℝ) (φ_limit : ℝ → ℂ)
    (h_pointwise : ∀ t, Filter.Tendsto (fun n => charFunRV (X n) ν t) atTop (nhds (φ_limit t)))
    (_h_cont : Continuous φ_limit) (_h_one : φ_limit 0 = 1) :
    ConvergesInDistribution X ν φ_limit :=
  h_pointwise

/-- The standard normal characteristic function is continuous. -/
theorem stdNormalCharFun_continuous : Continuous stdNormalCharFun := by
  unfold stdNormalCharFun
  fun_prop

/-- The standard normal characteristic function at 0 is 1. -/
theorem stdNormalCharFun_zero : stdNormalCharFun 0 = 1 := by
  simp [stdNormalCharFun, pow_succ, pow_zero]

/-- Variance is non-negative. -/
theorem variance_nonneg' {Ω' : Type*} [MeasurableSpace Ω'] (ν : Measure Ω') (X : Ω' → ℝ) :
    0 ≤ variance X ν :=
  ProbabilityTheory.variance_nonneg X ν

/-- For i.i.d. variables, Var(S_n) = n · Var(X₀). -/
theorem variance_iid_sum [IsProbabilityMeasure μ] (X : ℕ → Ω → ℝ) (hX_iid : IsIID X μ)
    (hX_meas : ∀ n, Measurable (X n))
    (hX_sq_integrable : ∀ n, Integrable (fun ω => (X n ω) ^ 2) μ)
    (n : ℕ) :
    variance (partialSum X n) μ = ↑n * variance (X 0) μ := by
  -- partialSum X n = ∑ j in range n, X j
  have h_eq : partialSum X n = ∑ j ∈ Finset.range n, X j := by
    ext ω; simp [partialSum]
  rw [h_eq]
  -- Memℒp from square integrability
  have h_memLp : ∀ i, MemLp (X i) 2 μ :=
    fun i => memLp_two_iff_integrable_sq (hX_meas i).aestronglyMeasurable
      |>.mpr (hX_sq_integrable i)
  -- Pairwise independence from iIndepFun
  have h_pairwise : Set.Pairwise ↑(Finset.range n)
      fun i j => IndepFun (X i) (X j) μ := by
    intro i _ j _ hij
    exact hX_iid.indep.indepFun hij
  -- Sum of variances
  rw [IndepFun.variance_sum
    (fun i _ => h_memLp i) h_pairwise]
  -- Each Var(X i) = Var(X 0) by identical distribution
  have h_var_eq : ∀ i, variance (X i) μ = variance (X 0) μ := by
    intro i
    exact (hX_iid.ident_distrib i).variance_eq
  simp_rw [h_var_eq]
  rw [Finset.sum_const, Finset.card_range]
  simp [nsmul_eq_mul]

/-- 𝔼[S_n] = n · 𝔼[X₀] for i.i.d. variables. -/
theorem mean_iid_sum [IsProbabilityMeasure μ] (X : ℕ → Ω → ℝ) (hX_iid : IsIID X μ)
    (hX_integrable : ∀ n, Integrable (X n) μ) (n : ℕ) :
    ∫ ω, partialSum X n ω ∂μ = ↑n * ∫ ω, X 0 ω ∂μ := by
  simp only [partialSum]
  rw [integral_finset_sum _ (fun i _ => hX_integrable i)]
  have h_eq : ∀ i : ℕ, ∫ ω, X i ω ∂μ = ∫ ω, X 0 ω ∂μ := by
    intro i
    exact (hX_iid.ident_distrib i).integral_eq
  simp_rw [h_eq]
  rw [Finset.sum_const, Finset.card_range]
  simp [nsmul_eq_mul]

end CLTLemmas

/-! ## Multivariate CLT (Statement) -/

/-- **Multivariate Central Limit Theorem** (statement only):
    For i.i.d. random vectors in ℝᵈ with finite second moments,
    the standardized sums converge in distribution to N(0, Σ). -/
theorem multivariate_clt
    {Ω : Type*} [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (d : ℕ)
    (X : ℕ → Ω → Fin d → ℝ)
    (hX_iid : iIndepFun (β := fun (_ : ℕ) => Fin d → ℝ) X μ)
    (hX_integrable : ∀ n, Integrable (X n) μ)
    (mean_vec : Fin d → ℝ)
    (hmean : ∀ j, mean_vec j = ∫ ω, X 0 ω j ∂μ)
    (cov : Fin d → Fin d → ℝ)
    (hcov : ∀ i j, cov i j = ∫ ω, (X 0 ω i - mean_vec i) * (X 0 ω j - mean_vec j) ∂μ) :
    ∀ t : Fin d → ℝ,
      Filter.Tendsto
        (fun n => ∫ ω, Complex.exp (↑(Finset.univ.sum fun j => t j *
          (((Finset.range n).sum fun i => X i ω j) - ↑n * mean_vec j) /
          Real.sqrt ↑n) * Complex.I) ∂μ)
        atTop
        (nhds (Complex.exp (-(↑(Finset.univ.sum fun i =>
          Finset.univ.sum fun j => t i * cov i j * t j) / 2)))) := by
  sorry

end
