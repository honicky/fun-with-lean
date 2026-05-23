#!/usr/bin/env python3
"""Per-domain accuracy analysis for MathArena competitions.

For one or more MathArena competitions, this joins the problem set (which carries
`problem_type` domain tags such as Algebra / Number Theory / Combinatorics /
Geometry) with the model-output logs (which carry a per-run `correct` flag) and
reports accuracy broken down by mathematical domain.

Data comes straight from the public HuggingFace datasets under the MathArena org:
  - problems:  MathArena/<competition>
  - outputs:   MathArena/<competition>_outputs

Only the columns needed for scoring are read, via parquet column projection over
HTTP, so the multi-gigabyte raw message logs are never downloaded.

Examples:
  python matharena_domain_analysis.py --competitions hmmt_feb_2026
  python matharena_domain_analysis.py --competitions hmmt_feb_2026 aime_2026 --csv out.csv
  python matharena_domain_analysis.py --competitions hmmt_feb_2026 --models GPT-5 Grok
  python matharena_domain_analysis.py --list
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfApi, HfFileSystem

_FS = HfFileSystem()
_API = HfApi()
_ORG = "MathArena"


def list_competitions() -> list[str]:
    """Return competitions that have both a problem set and an *_outputs set."""
    names = {d.id.split("/")[-1] for d in _API.list_datasets(author=_ORG)}
    return sorted(n[: -len("_outputs")] for n in names if n.endswith("_outputs")
                  and n[: -len("_outputs")] in names)


def _read_columns(repo: str, columns: list[str]) -> pd.DataFrame:
    matches = _FS.glob(f"datasets/{_ORG}/{repo}/data/*.parquet")
    if not matches:
        raise FileNotFoundError(f"no parquet files found for dataset "
                                f"'{_ORG}/{repo}'")
    frames = [pq.read_table(m, columns=columns, filesystem=_FS).to_pandas()
              for m in matches]
    return pd.concat(frames, ignore_index=True)


def _domains(value) -> list[str]:
    """Normalize a problem_type cell into a clean list of domain tags.

    Tags arrive as a list but individual entries can carry stray whitespace
    (e.g. 'Combinatorics,  Number Theory' is stored as two tags, the second
    with a leading space), so each tag is stripped and empties are dropped.
    """
    if value is None:
        return []
    items = value.tolist() if hasattr(value, "tolist") else list(value)
    return [t.strip() for t in items if t and t.strip()]


def load_competition(competition: str) -> pd.DataFrame:
    """Return one row per (model, problem, run) with its domain tags attached.

    The returned frame is already exploded on domain: a problem tagged with two
    domains yields two rows per run, so multi-domain problems count toward each
    of their domains (matching MathArena's own domain breakdown).
    """
    problems = _read_columns(competition, ["problem_idx", "problem_type"])
    outputs = _read_columns(f"{competition}_outputs",
                            ["problem_idx", "model_name", "model_config",
                             "idx_answer", "correct"])

    problems["domains"] = problems["problem_type"].map(_domains)
    # problem_idx is int in the problem set but str in the outputs; align on str.
    problems["problem_idx"] = problems["problem_idx"].astype(str)
    outputs["problem_idx"] = outputs["problem_idx"].astype(str)

    merged = outputs.merge(problems[["problem_idx", "domains"]],
                           on="problem_idx", how="left")
    missing = merged["domains"].isna().sum()
    if missing:
        print(f"  [warn] {competition}: {missing} output rows had no matching "
              f"problem and were dropped", file=sys.stderr)
        merged = merged[merged["domains"].notna()]

    merged = merged.explode("domains").rename(columns={"domains": "domain"})
    merged = merged[merged["domain"].notna() & (merged["domain"] != "")]
    merged["competition"] = competition
    return merged


def aggregate(runs: pd.DataFrame) -> pd.DataFrame:
    """Collapse run-level rows into (model, domain) accuracy stats."""
    g = runs.groupby(["model_name", "model_config", "domain"], as_index=False)
    out = g.agg(n_runs=("correct", "size"),
                n_correct=("correct", "sum"),
                n_problems=("problem_idx", "nunique"))
    out["accuracy"] = out["n_correct"] / out["n_runs"]
    return out


def _pct(x: float) -> str:
    return f"{100 * x:5.1f}"


def print_report(runs: pd.DataFrame, agg: pd.DataFrame) -> None:
    domains = sorted(runs["domain"].unique())

    print("\n" + "=" * 72)
    print("DOMAIN SUMMARY (all models pooled)")
    print("=" * 72)
    pooled = (runs.groupby("domain")
              .agg(n_problems=("problem_idx", "nunique"),
                   n_runs=("correct", "size"),
                   accuracy=("correct", "mean"))
              .reindex(domains))
    pooled["accuracy"] = pooled["accuracy"].map(_pct)
    print(pooled.to_string())

    print("\n" + "=" * 72)
    print("ACCURACY (%) BY MODEL x DOMAIN")
    print("=" * 72)
    pivot = agg.pivot_table(index="model_name", columns="domain",
                            values="accuracy")
    overall = runs.groupby("model_name")["correct"].mean().rename("Overall")
    pivot = pivot.join(overall).sort_values("Overall", ascending=False)
    print((100 * pivot).round(1).to_string())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--competitions", nargs="+", default=["hmmt_feb_2026"],
                    help="MathArena competition name(s), e.g. hmmt_feb_2026 aime_2026")
    ap.add_argument("--models", nargs="*", default=None,
                    help="optional substring filter(s) on model name")
    ap.add_argument("--csv", default=None,
                    help="write the long-format (model, domain) table to this path")
    ap.add_argument("--list", action="store_true",
                    help="list available competitions and exit")
    args = ap.parse_args()

    if args.list:
        for c in list_competitions():
            print(c)
        return 0

    all_runs = []
    for comp in args.competitions:
        print(f"Loading {comp} ...", file=sys.stderr)
        try:
            all_runs.append(load_competition(comp))
        except Exception as e:  # noqa: BLE001 - report and continue to next comp
            print(f"  [skip] {comp}: {e}", file=sys.stderr)
    if not all_runs:
        print("No data loaded.", file=sys.stderr)
        return 1

    runs = pd.concat(all_runs, ignore_index=True)
    if args.models:
        mask = pd.Series(False, index=runs.index)
        for needle in args.models:
            mask |= runs["model_name"].str.contains(needle, case=False, na=False)
        runs = runs[mask]
        if runs.empty:
            print(f"No models matched {args.models}.", file=sys.stderr)
            return 1

    label = ", ".join(args.competitions)
    print(f"\nCompetitions: {label}")
    print(f"Models: {runs['model_name'].nunique()} | "
          f"Problems: {runs['problem_idx'].nunique()} | "
          f"Run-level rows: {len(runs)}")

    agg = aggregate(runs)
    print_report(runs, agg)

    if args.csv:
        agg_out = agg.sort_values(["model_name", "domain"])
        agg_out.to_csv(args.csv, index=False)
        print(f"\nWrote {len(agg_out)} rows to {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
