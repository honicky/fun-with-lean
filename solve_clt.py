#!/usr/bin/env python3
"""Use AXLE API to verify and fill sorrys in the CLT proof."""

import asyncio
import json
import sys
from pathlib import Path

from axle.client import AxleClient

LEAN_FILE = Path(__file__).parent / "CentralLimitTheorem.lean"
ENVIRONMENT = "lean-4.28.0"


async def main() -> int:
    lean_code = LEAN_FILE.read_text()
    print(f"File: {LEAN_FILE.name} ({len(lean_code)} chars)")

    async with AxleClient() as client:
        # Step 1: Check the file
        print("\n[1] Checking Lean code...")
        result = await client.check(content=lean_code, environment=ENVIRONMENT)
        print(f"  Status: {'PASS' if result.okay else 'FAIL'}")
        if result.lean_messages:
            for attr in ['errors', 'warnings']:
                msgs = getattr(result.lean_messages, attr, [])
                if msgs:
                    print(f"  {attr.title()} ({len(msgs)}):")
                    for m in msgs[:10]:
                        print(f"    {m}")

        # Step 2: Extract theorems
        print("\n[2] Extracting theorems...")
        extracted = await client.extract_theorems(
            content=lean_code, environment=ENVIRONMENT
        )
        if extracted.documents:
            for name, doc in extracted.documents.items():
                marker = " [sorry]" if doc.is_sorry else " [proved]"
                print(f"  {doc.type:10s} {name}{marker}")

        # Step 3: sorry2lemma - extract sorry goals as standalone lemmas
        print("\n[3] Extracting sorry goals to standalone lemmas...")
        sorry_result = await client.sorry2lemma(
            content=lean_code,
            environment=ENVIRONMENT,
        )
        print(f"  Response type: {type(sorry_result)}")
        # Print what we get back
        for attr in dir(sorry_result):
            if not attr.startswith('_'):
                val = getattr(sorry_result, attr)
                if not callable(val):
                    if isinstance(val, str) and len(val) > 500:
                        print(f"  {attr}: {val[:500]}...")
                    else:
                        print(f"  {attr}: {val}")

        # Step 4: Try repair_proofs on the sorry theorems
        print("\n[4] Attempting to repair proofs...")
        repair_result = await client.repair_proofs(
            content=lean_code,
            environment=ENVIRONMENT,
            names=["CLTLemmas.charFunRV_taylor"],
        )
        print(f"  Response type: {type(repair_result)}")
        for attr in dir(repair_result):
            if not attr.startswith('_'):
                val = getattr(repair_result, attr)
                if not callable(val):
                    if isinstance(val, str) and len(val) > 500:
                        print(f"  {attr}: {val[:500]}...")
                    else:
                        print(f"  {attr}: {val}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
