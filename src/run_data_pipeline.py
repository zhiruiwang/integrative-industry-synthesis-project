"""
Run the full data pipeline: O*NET + BLS OES + BLS projections -> data/occupations.csv.
Provides refresh-data when run as main; use the Streamlit app for recommendations and roadmaps.
"""
import argparse
import csv
from pathlib import Path
from typing import Optional

from src.data_pipeline.process_onet import process_onet_occupations_and_skills
from src.data_pipeline.process_bls_projections import process_bls_projections_growth
from src.data_pipeline.process_bls_oes import process_bls_oes_wages
from src.data_pipeline.merge import merge_occupations


def run_data_pipeline(
    data_dir: Optional[Path] = None,
    max_occupations: Optional[int] = None,
) -> list[dict]:
    """
    Load O*NET (data/onet/), BLS OES (data/bls_oes/), BLS projections (data/bls_projections/);
    merge; write data/occupations.csv. Returns merged list. Raises if O*NET fails or merge is empty.
    """
    base = Path(__file__).resolve().parent.parent
    data_dir = data_dir or base / "data"
    out_path = data_dir / "occupations.csv"

    onet_dir = data_dir / "onet"
    onet_titles, onet_skills, _, onet_extras = process_onet_occupations_and_skills(onet_dir=onet_dir)
    if not onet_titles:
        raise RuntimeError("O*NET process returned no occupations. Check network and data/onet/.")

    bls_wages = {}
    try:
        bulk = process_bls_oes_wages(data_dir=data_dir / "bls_oes")
        for soc, v in bulk.items():
            wage = v.get("median_salary") or v.get("mean_annual_wage")
            if wage:
                bls_wages[soc] = {
                    "mean_annual_wage": v.get("mean_annual_wage"),
                    "median_salary": v.get("median_salary"),
                    "title": v.get("title"),
                }
    except Exception:
        pass

    growth = {}
    try:
        growth = process_bls_projections_growth(data_dir=data_dir / "bls_projections")
    except Exception:
        pass

    merged = merge_occupations(
        bls_wages=bls_wages,
        onet_titles=onet_titles,
        onet_skills=onet_skills,
        growth=growth,
        max_occupations=max_occupations,
        onet_extras=onet_extras,
    )
    if not merged:
        raise RuntimeError("Merge produced no occupations.")

    data_dir.mkdir(parents=True, exist_ok=True)
    keys = list(merged[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for row in merged:
            w.writerow({k: (v if v is not None else "") for k, v in row.items()})
    return merged


def _cmd_refresh_data(args):
    base = Path(__file__).resolve().parent.parent
    print("Fetching O*NET occupations and skills...")
    print("Loading BLS OES wages and employment projections from data/...")
    occs = run_data_pipeline(data_dir=base / "data", max_occupations=getattr(args, "max", None))
    print(f"Wrote {len(occs)} occupations to data/occupations.csv")
    wages = sum(1 for o in occs if o.get("median_salary"))
    growth = sum(1 for o in occs if o.get("growth_pct"))
    print(f"  With BLS wage data: {wages}  |  With growth data: {growth}")


def main():
    p = argparse.ArgumentParser(
        description="AI Career Pathway & Labor Market Intelligence Platform – data refresh",
        prog="python -m src.run_data_pipeline",
    )
    sub = p.add_subparsers(dest="command", help="Commands")
    r = sub.add_parser("refresh-data", help="Fetch O*NET + BLS and rebuild occupation data")
    r.add_argument("--max", type=int, default=None, help="Limit to N occupations (default: no limit)")
    r.set_defaults(func=_cmd_refresh_data)

    args = p.parse_args()
    if not args.command:
        p.print_help()
        print("\nExample: python -m src.run_data_pipeline refresh-data")
        return
    args.func(args)


if __name__ == "__main__":
    main()
