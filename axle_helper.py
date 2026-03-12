#!/usr/bin/env python3
"""Helper to use AXLE API for CLT proof development."""

import asyncio
import sys
from pathlib import Path

from axle.client import AxleClient

LEAN_FILE = Path(__file__).parent / "CentralLimitTheorem.lean"
ENVIRONMENT = "lean-4.28.0"


async def check_file(path: str | None = None):
    """Check a Lean file for errors."""
    p = Path(path) if path else LEAN_FILE
    code = p.read_text()
    async with AxleClient() as client:
        result = await client.check(content=code, environment=ENVIRONMENT)
        if result.okay:
            sorry_count = sum(1 for w in result.lean_messages.warnings if "sorry" in w)
            print(f"PASS ({sorry_count} sorry warnings)")
        else:
            print("FAIL")
            for e in result.lean_messages.errors:
                print(f"  ERROR: {e.strip()}")
        for w in result.lean_messages.warnings:
            if "sorry" not in w:
                print(f"  WARN: {w.strip()}")


async def sorry2lemma_file(path: str | None = None):
    """Extract sorrys as standalone lemmas."""
    p = Path(path) if path else LEAN_FILE
    code = p.read_text()
    async with AxleClient() as client:
        result = await client.sorry2lemma(content=code, environment=ENVIRONMENT)
        print(f"Extracted lemmas: {result.lemma_names}")
        # Write the transformed content
        out = p.with_suffix('.sorry2lemma.lean')
        out.write_text(result.content)
        print(f"Written to {out}")


async def repair_file(path: str | None = None, names: list[str] | None = None):
    """Try to repair proofs."""
    p = Path(path) if path else LEAN_FILE
    code = p.read_text()
    async with AxleClient() as client:
        result = await client.repair_proofs(
            content=code, environment=ENVIRONMENT, names=names
        )
        print(f"Repair stats: {result.repair_stats}")
        if result.content != code:
            out = p.with_suffix('.repaired.lean')
            out.write_text(result.content)
            print(f"Changes written to {out}")
        else:
            print("No changes made")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    path = sys.argv[2] if len(sys.argv) > 2 else None
    names = sys.argv[3:] if len(sys.argv) > 3 else None

    if cmd == "check":
        asyncio.run(check_file(path))
    elif cmd == "sorry2lemma":
        asyncio.run(sorry2lemma_file(path))
    elif cmd == "repair":
        asyncio.run(repair_file(path, names))
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python3 axle_helper.py [check|sorry2lemma|repair] [file] [names...]")
