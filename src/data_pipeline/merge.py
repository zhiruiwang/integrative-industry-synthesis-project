"""
Merge O*NET (titles, skills, abilities, knowledge, work_activities, interests, job_zone),
BLS OES wages, and BLS projections into a single occupation table.

Only occupations that have at least one O*NET skill and valid BLS wage data are included.
Output: data/occupations.csv with id, title, skills, median_salary, growth_pct, education,
sector, and optional abilities, knowledge, work_activities, interests, job_zone.
"""
from typing import Optional

from .soc import normalize_soc

# Top-N list lengths for O*NET extras (skills/abilities/knowledge/work_activities use 7; interests 6).
_MAX_SKILLS_ABILITIES_KNOWLEDGE_WORK = 7
_MAX_INTERESTS = 6


def _list_to_str(lst, max_items: int = 10):
    """Join list to comma-separated string; truncate to max_items. None if empty."""
    if not lst:
        return None
    return ", ".join(lst[:max_items])


def merge_occupations(
    bls_wages: dict,
    onet_titles: dict,
    onet_skills: dict,
    growth: dict,
    max_occupations: Optional[int] = None,
    onet_extras: Optional[dict] = None,
) -> list[dict]:
    """
    Merge by SOC. Keeps only rows with at least one skill and wage > 0.
    Returns list of dicts with id, title, skills, median_salary, growth_pct, education, sector,
    and when onet_extras given: abilities, knowledge, work_activities, interests, job_zone.
    """
    onet_extras = onet_extras or {}
    onet_norm = {normalize_soc(k): v for k, v in onet_titles.items()}
    skills_norm = {normalize_soc(k): v for k, v in onet_skills.items()}
    bls_norm = {normalize_soc(k): v for k, v in bls_wages.items()}
    growth_norm = {normalize_soc(k): v for k, v in growth.items()}
    abilities_norm = {normalize_soc(k): v for k, v in onet_extras.get("abilities", {}).items()}
    knowledge_norm = {normalize_soc(k): v for k, v in onet_extras.get("knowledge", {}).items()}
    work_activities_norm = {normalize_soc(k): v for k, v in onet_extras.get("work_activities", {}).items()}
    interests_norm = {normalize_soc(k): v for k, v in onet_extras.get("interests", {}).items()}
    job_zone_norm = {normalize_soc(k): v for k, v in onet_extras.get("job_zone", {}).items()}
    all_codes = set(onet_norm.keys()) | set(bls_norm.keys())

    merged = []
    for c in all_codes:
        skill_list = skills_norm.get(c) or []
        if not skill_list:
            continue
        raw_title = onet_norm.get(c) or (bls_norm.get(c) or {}).get("title") or c
        title = None if (raw_title == c or not raw_title.strip()) else raw_title
        wage_info = bls_norm.get(c) or {}
        wage = wage_info.get("median_salary") or wage_info.get("mean_annual_wage")
        if wage is None or wage <= 0:
            continue
        skills_str = ", ".join(skill_list)
        growth_pct = growth_norm.get(c)
        if growth_pct is not None:
            growth_pct = float(growth_pct)
        sector = c[:2] if len(c) >= 2 else ""

        rec = {
            "id": c,
            "title": title,
            "skills": skills_str,
            "median_salary": int(wage),
            "growth_pct": growth_pct,
            "education": "bachelor",
            "sector": sector,
        }
        if abilities_norm:
            rec["abilities"] = _list_to_str(abilities_norm.get(c), max_items=_MAX_SKILLS_ABILITIES_KNOWLEDGE_WORK)
        if knowledge_norm:
            rec["knowledge"] = _list_to_str(knowledge_norm.get(c), max_items=_MAX_SKILLS_ABILITIES_KNOWLEDGE_WORK)
        if work_activities_norm:
            rec["work_activities"] = _list_to_str(work_activities_norm.get(c), max_items=_MAX_SKILLS_ABILITIES_KNOWLEDGE_WORK)
        if interests_norm:
            rec["interests"] = _list_to_str(interests_norm.get(c), max_items=_MAX_INTERESTS)
        if job_zone_norm:
            rec["job_zone"] = job_zone_norm.get(c)
        merged.append(rec)

    merged.sort(key=lambda x: -x["median_salary"])
    if max_occupations is not None:
        merged = merged[:max_occupations]
    return merged
