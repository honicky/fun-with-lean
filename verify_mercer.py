#!/usr/bin/env python3
"""
Verify the Lean 4 formalization of Mercer's Theorem using AXLE.

Usage:
    export AXLE_API_KEY=your-key  # optional, for higher rate limits
    python3 verify_mercer.py
"""

import asyncio
import sys
from pathlib import Path

from axle import AxleClient

LEAN_FILE = Path(__file__).parent / "MercersTheorem.lean"
ENVIRONMENT = "lean-4.28.0"


async def main() -> int:
    lean_code = LEAN_FILE.read_text()
    print(f"Verifying {LEAN_FILE.name} ({len(lean_code)} chars) against {ENVIRONMENT}...")

    async with AxleClient() as client:
        # Step 1: Check the full file compiles
        print("\n[1/3] Checking Lean code...")
        result = await client.check(content=lean_code, environment=ENVIRONMENT)
        print(f"  Status: {'PASS' if result.okay else 'FAIL'}")

        if result.lean_messages.errors:
            print(f"\n  Errors ({len(result.lean_messages.errors)}):")
            for err in result.lean_messages.errors:
                print(f"    {err}")

        sorry_count = sum(1 for w in result.lean_messages.warnings if "sorry" in w)
        if sorry_count:
            print(f"  Declarations using sorry: {sorry_count}")

        if not result.okay:
            print("\nFAILED: Lean code has errors.")
            return 1

        # Step 2: Extract theorems to get structured info
        print("\n[2/3] Extracting theorems...")
        extracted = await client.extract_theorems(content=lean_code, environment=ENVIRONMENT)

        if extracted.documents:
            print(f"  Found {len(extracted.documents)} declarations:")
            for name, doc in extracted.documents.items():
                sorry_marker = " [sorry]" if doc.is_sorry else " [proved]"
                print(f"    {doc.type:10s} {name}{sorry_marker}")
        else:
            print("  No declarations extracted.")

        # Step 3: Verify the main theorem statement is well-formed
        print("\n[3/3] Verifying main theorem statement...")
        main_theorem = """import Mathlib
open MeasureTheory Filter Topology Set Finset
noncomputable section
abbrev I := Set.Icc (0 : ℝ) 1
instance : CompactSpace I := by apply isCompact_iff_compactSpace.mp; exact isCompact_Icc
def μI : Measure I := Measure.comap Subtype.val volume
structure ContinuousKernel where
  toFun : I → I → ℝ
  continuous_toFun : Continuous (fun p : I × I => toFun p.1 p.2)
namespace ContinuousKernel
variable (K : ContinuousKernel)
def IsSymmetric : Prop := ∀ s t : I, K.toFun s t = K.toFun t s
def IsPositiveDefinite : Prop :=
  ∀ f : I → ℝ, Continuous f → 0 ≤ ∫ s : I, ∫ t : I, K.toFun s t * f s * f t ∂μI ∂μI
structure IsMercer : Prop where
  symmetric : K.IsSymmetric
  pos_def : K.IsPositiveDefinite
def integralOperator (f : I → ℝ) (s : I) : ℝ := ∫ t : I, K.toFun s t * f t ∂μI
structure Eigenfunction where
  func : I → ℝ
  eigenvalue : ℝ
  continuous_func : Continuous func
  is_eigen : ∀ s : I, K.integralOperator func s = eigenvalue * func s
  normalized : ∫ s : I, func s ^ 2 ∂μI = 1
structure SpectralDecomposition where
  eigenfunctions : ℕ → K.Eigenfunction
  eigenvalues_nonneg : ∀ n, (eigenfunctions n).eigenvalue ≥ 0
  eigenvalues_decreasing : ∀ n, (eigenfunctions (n+1)).eigenvalue ≤ (eigenfunctions n).eigenvalue
  orthonormal : ∀ m n, m ≠ n → ∫ s : I, (eigenfunctions m).func s * (eigenfunctions n).func s ∂μI = 0
end ContinuousKernel

-- Verify the main theorem statement type-checks
theorem mercers_theorem (K : ContinuousKernel) (hK : K.IsMercer) :
    ∃ (S : K.SpectralDecomposition),
      Summable (fun n => (S.eigenfunctions n).eigenvalue) ∧
      TendstoUniformly
        (fun (N : ℕ) (p : I × I) =>
          (Finset.range N).sum fun n =>
            (S.eigenfunctions n).eigenvalue *
            (S.eigenfunctions n).func p.1 *
            (S.eigenfunctions n).func p.2)
        (fun p => K.toFun p.1 p.2)
        atTop := by sorry
end
"""
        verify_result = await client.check(content=main_theorem, environment=ENVIRONMENT)
        print(f"  Main theorem statement: {'WELL-FORMED' if verify_result.okay else 'MALFORMED'}")
        if verify_result.lean_messages.errors:
            for err in verify_result.lean_messages.errors:
                print(f"    {err}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  File: {LEAN_FILE.name}")
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Code check: {'PASS' if result.okay else 'FAIL'}")
    print(f"  Declarations: {len(extracted.documents) if extracted.documents else 0}")
    print(f"  Sorry count: {sorry_count}")
    print(f"  Theorem statement: {'WELL-FORMED' if verify_result.okay else 'MALFORMED'}")
    print("=" * 60)

    return 0 if result.okay else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
