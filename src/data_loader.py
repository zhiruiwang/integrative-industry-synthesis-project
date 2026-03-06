"""Load occupation data from data/occupations.csv (pipeline output)."""
import csv
from pathlib import Path
from typing import List, Optional


def load_occupations(data_dir: str = "data", ensure_data: bool = True) -> list[dict]:
    """
    Load occupations from data/occupations.csv. If missing and ensure_data is True,
    runs the data pipeline once then retries. Raises if still no data.
    """
    base = Path(__file__).resolve().parent.parent
    data_path = base / data_dir
    out_path = data_path / "occupations.csv"

    def _load() -> Optional[List[dict]]:
        if not out_path.exists():
            return None
        try:
            with open(out_path, encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            if not rows:
                return None
            for row in rows:
                for k, v in row.items():
                    if v == "":
                        row[k] = None
                    elif k in ("median_salary", "job_zone") and v is not None:
                        try:
                            row[k] = int(float(v))
                        except (TypeError, ValueError):
                            pass
                    elif k == "growth_pct" and v is not None:
                        try:
                            row[k] = float(v)
                        except (TypeError, ValueError):
                            pass
            return rows
        except (OSError, csv.Error):
            return None

    data = _load()
    if data is not None:
        return data
    if ensure_data:
        from .run_data_pipeline import run_data_pipeline
        run_data_pipeline(data_dir=data_path)
        data = _load()
        if data is not None:
            return data

    raise FileNotFoundError(
        "No occupation data found. Run: python -m src.run_data_pipeline refresh-data"
    )
