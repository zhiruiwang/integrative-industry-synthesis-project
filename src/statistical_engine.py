"""
Component 1: Statistical Labor Market Analysis (Capstone 2 – Statistical Analysis).
Computes per-occupation metrics from real BLS/O*NET data: salary percentiles,
growth scores, and risk-adjusted opportunity.
"""
import numpy as np


def compute_labor_market_metrics(occupations: list[dict]) -> dict[str, dict]:
    """
    Compute per-occupation statistics: growth score, salary percentiles (approximate),
    and risk-adjusted opportunity score.
    """
    # median_salary may be missing in older CSVs; use 0 for missing so stats still compute
    salaries = np.array([o.get("median_salary") if o.get("median_salary") is not None else 0 for o in occupations])
    # growth_pct may be None (missing); use nan for stats so we don't treat missing as 0
    growths = np.array([o["growth_pct"] if o.get("growth_pct") is not None else np.nan for o in occupations])
    salary_mean, salary_std = salaries.mean(), salaries.std()
    growth_mean = np.nanmean(growths) if np.any(~np.isnan(growths)) else 0.0
    growth_std = np.nanstd(growths) if np.any(~np.isnan(growths)) else 1.0
    if salary_mean <= 0:
        salary_mean = 1.0
    if salary_std <= 0:
        salary_std = 1.0
    if growth_std <= 0:
        growth_std = 1.0

    results = {}
    for o in occupations:
        occ_id = o["id"]
        sal = o.get("median_salary") if o.get("median_salary") is not None else 0
        gr = o.get("growth_pct")
        gr_val = float(gr) if gr is not None else np.nan
        # Approximate percentile (0-100) from position in sample
        salary_pct = max(0, min(100, 50 + (sal - salary_mean) / (salary_std + 1e-6) * 15))
        growth_score = (gr_val - growth_mean) / (growth_std + 1e-6) if not np.isnan(gr_val) else 0.0
        # Risk-adjusted: balance salary and growth (simplified); use 0 for missing growth
        risk_adjusted = 0.6 * (sal / salary_mean) + 0.4 * (1 + growth_score * 0.2)
        results[occ_id] = {
            "growth_score": gr_val if not np.isnan(gr_val) else None,
            "salary_percentile_approx": float(np.clip(salary_pct, 0, 100)),
            "risk_adjusted_opportunity": float(np.clip(risk_adjusted, 0, 2)),
            "median_salary": sal,
            "growth_pct": gr,
        }
    return results
