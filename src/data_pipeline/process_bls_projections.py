"""
Process BLS employment growth (percent change) from data/bls_projections/occupation.xlsx.

Reads Table 1.2 (2024–2034 projections); header in row 1. Returns SOC -> growth_pct.
"""
from pathlib import Path
from typing import Optional

from .soc import normalize_soc


def process_bls_projections_growth(
    data_dir: Optional[Path] = None,
) -> dict[str, float]:
    """
    Load employment growth (percent change) by occupation from XLSX in data_dir
    (default data/bls_projections). Returns dict mapping SOC to growth_pct.
    """
    data_dir = data_dir or (
        Path(__file__).resolve().parent.parent.parent / "data" / "bls_projections"
    )
    out = {}
    xlsx_path = data_dir / "occupation.xlsx"
    if not xlsx_path.exists():
        return out
    try:
        import pandas as pd
    except ImportError:
        return out
    try:
        xl = pd.ExcelFile(xlsx_path)
        sheet_name = None
        for candidate in ("Table 1.2", "1.2"):
            if candidate in xl.sheet_names:
                sheet_name = candidate
                break
        if sheet_name is None:
            sheet_name = 0
        header_row = 1 if (isinstance(sheet_name, str) and "1.2" in str(sheet_name)) else 0
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=header_row)
        cols = [c for c in df.columns if c is not None and str(c).strip()]
        code_col = None
        for name in ("2024 national employment matrix code", "matrix code", "occupation code", "O*NET-SOC", "OCC_CODE", "Occupation Code", "occupation_code", "SOC", "Code"):
            for c in cols:
                if name.lower() in str(c).lower():
                    code_col = c
                    break
            if code_col is not None:
                break
        if code_col is None:
            code_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        pct_col = None
        for c in cols:
            if "employment change" in str(c).lower() and "percent" in str(c).lower():
                pct_col = c
                break
        if pct_col is None:
            for c in cols:
                if "employment change, percent" in str(c).lower() or "employment change" in str(c).lower():
                    pct_col = c
                    break
        if pct_col is None:
            for c in cols:
                if "percent" in str(c).lower() or "growth" in str(c).lower() or "change" in str(c).lower():
                    pct_col = c
                    break
        if pct_col is None:
            e24 = e34 = None
            for c in cols:
                if "2024" in str(c) and "employ" in str(c).lower() and "change" not in str(c).lower():
                    e24 = c
                if "2034" in str(c) and "employ" in str(c).lower():
                    e34 = c
            if e24 and e34:
                for _, row in df.iterrows():
                    try:
                        code = str(row.get(code_col, "")).strip()
                        v24 = float(row.get(e24, 0) or 0)
                        v34 = float(row.get(e34, 0) or 0)
                        if code and code != "—" and v24 and v24 > 0:
                            out[normalize_soc(code)] = round((v34 - v24) / v24 * 100, 1)
                    except (TypeError, ValueError):
                        continue
                return out
            return out
        for _, row in df.iterrows():
            try:
                code = str(row.get(code_col, "")).strip()
                if not code or code == "—" or code.lower() == "nan":
                    continue
                pct = row.get(pct_col)
                if pct is None or (isinstance(pct, float) and pd.isna(pct)):
                    continue
                pct = float(pct)
                out[normalize_soc(code)] = round(pct, 1)
            except (TypeError, ValueError):
                continue
    except Exception:
        pass
    return out
