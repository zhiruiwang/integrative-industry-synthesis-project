"""
Process BLS OES wages from local XLSX (e.g. national_M2024_dl.xlsx in data/bls_oes/).

Uses A_MEDIAN (annual median), else H_MEDIAN*2080, else A_MEAN. Keeps only cross-industry (NAICS=0)
when the NAICS column is present. Returns SOC -> {title, mean_annual_wage}.
"""
from pathlib import Path
from typing import Optional

from .soc import normalize_soc


def _parse_wage(val) -> Optional[int]:
    """Parse wage from cell: number, or string with $ and commas."""
    if val is None:
        return None
    if isinstance(val, float):
        if val != val or val <= 0:  # NaN or non-positive
            return None
        return int(val)
    s = str(val).strip().replace("$", "").replace(",", "")
    if not s or s.lower() == "nan":
        return None
    try:
        w = float(s)
        return int(w) if w > 0 else None
    except ValueError:
        return None


def process_bls_oes_wages(
    data_dir: Optional[Path] = None,
) -> dict[str, dict]:
    """
    Load wage by occupation from XLSX in data_dir (default data/bls_oes).
    Prefers median annual wage when present (e.g. national_M2024_dl.xlsx); else mean annual wage.
    Returns dict mapping SOC (e.g. '15-1252.00') to {occupation_code, title, mean_annual_wage?, median_salary?}.
    """
    data_dir = data_dir or (
        Path(__file__).resolve().parent.parent.parent / "data" / "bls_oes"
    )
    out = {}
    try:
        import pandas as pd
    except ImportError:
        return out
    xlsx_files = list(data_dir.glob("*.xlsx")) if data_dir.exists() else []
    if not xlsx_files:
        return out
    for xlsx_path in xlsx_files:
        for header_row in (0, 1):
            try:
                df = pd.read_excel(xlsx_path, sheet_name=0, header=header_row)
            except Exception:
                continue
            cols = [c for c in df.columns if c is not None and str(c).strip()]
            if not cols:
                continue
            code_col = None
            for name in ("O*NET-SOC", "OCC_CODE", "occ_code", "Occupation Code", "occupation code", "SOC Code", "SOC", "Code"):
                for c in cols:
                    if name.lower() in str(c).lower():
                        code_col = c
                        break
                if code_col is not None:
                    break
            if code_col is None:
                code_col = df.columns[0]
            median_annual_col = None
            for name in ("A_MEDIAN", "median annual wage", "annual median wage", "annual_median_wage"):
                for c in cols:
                    if name.lower() in str(c).lower():
                        median_annual_col = c
                        break
                if median_annual_col is not None:
                    break
            if median_annual_col is None:
                for c in cols:
                    cl = str(c).lower()
                    if "median" in cl and ("annual" in cl or cl == "a_median"):
                        median_annual_col = c
                        break
            median_hourly_col = None
            for name in ("H_MEDIAN", "median hourly wage", "hourly median wage"):
                for c in cols:
                    if name.lower() in str(c).lower():
                        median_hourly_col = c
                        break
                if median_hourly_col is not None:
                    break
            if median_hourly_col is None:
                for c in cols:
                    cl = str(c).lower()
                    if "median" in cl and "hourly" in cl:
                        median_hourly_col = c
                        break
            mean_annual_col = None
            for name in ("annual mean wage", "mean annual wage", "annual_mean_wage", "mean_annual_wage", "A_MEAN"):
                for c in cols:
                    if name.lower() in str(c).lower():
                        mean_annual_col = c
                        break
                if mean_annual_col is not None:
                    break
            if mean_annual_col is None:
                for c in cols:
                    if "mean" in str(c).lower() and "wage" in str(c).lower() and "annual" in str(c).lower():
                        mean_annual_col = c
                        break
            wage_col = median_annual_col or median_hourly_col or mean_annual_col
            if wage_col is None:
                continue
            title_col = None
            for name in ("OCC_TITLE", "occ_title", "title", "occupation_title", "occupation title"):
                for c in cols:
                    if name.lower() in str(c).lower():
                        title_col = c
                        break
                if title_col is not None:
                    break
            naics_col = None
            for c in cols:
                if str(c).upper() == "NAICS":
                    naics_col = c
                    break
            for _, row in df.iterrows():
                try:
                    if naics_col is not None:
                        naics_val = row.get(naics_col)
                        if naics_val is not None and str(naics_val).strip() not in ("0", "0.0", ""):
                            try:
                                if int(float(naics_val)) != 0:
                                    continue
                            except (TypeError, ValueError):
                                continue
                    code = str(row.get(code_col, "")).strip()
                    if not code or code.lower() in ("nan", "soc", "code", "occupation code", "occ_code"):
                        continue
                    soc = normalize_soc(code)
                    wage = None
                    if median_annual_col is not None:
                        wage = _parse_wage(row.get(median_annual_col))
                    if wage is None and median_hourly_col is not None:
                        hourly = _parse_wage(row.get(median_hourly_col))
                        if hourly is not None:
                            wage = int(hourly * 2080)
                    if wage is None and mean_annual_col is not None:
                        wage = _parse_wage(row.get(mean_annual_col))
                    if wage is None or wage <= 0:
                        continue
                    title = ""
                    if title_col is not None:
                        title = str(row.get(title_col, "")).strip()
                    rec = {"occupation_code": soc, "title": title or soc}
                    if median_annual_col or median_hourly_col:
                        rec["median_salary"] = wage
                    rec["mean_annual_wage"] = wage
                    out[soc] = rec
                except (TypeError, ValueError):
                    continue
            if out:
                break
        if out:
            break
    return out
