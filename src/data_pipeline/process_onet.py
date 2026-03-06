"""
Process O*NET occupation data: titles, skills (by importance), and optional extras.

Reads from data/onet/ (downloads and extracts the text ZIP from onetcenter.org if missing).
Extracted files are kept; the zip is deleted after extract. Supports:
- Occupation Data.txt, Skills.txt (top 7 by importance)
- Abilities.txt, Knowledge.txt, Work Activities.txt (top 7 by importance)
- Interests.txt (RIASEC), Job Zones.txt (1–5)
"""
import csv
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
from io import StringIO

import requests

ONET_TEXT_ZIP_URL = "https://onetcenter.org/dl_files/database/db_28_2_text.zip"
TOP_N_ELEMENTS = 7  # skills, abilities, knowledge, work_activities


def _find_file_in_dir(
    root: Path,
    filename: str,
    exclude_containing: Optional[str] = None,
) -> Optional[Path]:
    """Find a file by name under root (recursive); optionally exclude paths containing a substring."""
    if not root.exists():
        return None
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if exclude_containing and exclude_containing in path.as_posix():
            continue
        if path.name == filename or path.name.lower() == filename.lower():
            return path
    return None


def _download_and_extract_to(url: str, target_dir: Path) -> None:
    """Download ZIP from url, extract into target_dir, then delete the zip file."""
    target_dir.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(r.content)
        zip_path = Path(tmp.name)
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(target_dir)
    finally:
        zip_path.unlink(missing_ok=True)


def _read_occupation_data(occ_path: Path) -> dict[str, str]:
    """Parse Occupation Data file (tab-delimited); return SOC code -> title."""
    titles = {}
    raw = occ_path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(StringIO(raw), delimiter="\t")
    for row in reader:
        code = (row.get("O*NET-SOC Code") or row.get("onet_soc_code") or row.get("code") or "").strip()
        title = (row.get("Title") or row.get("title") or "").strip()
        if code:
            titles[code] = title or code
    return titles


def _read_skills(skills_path: Path, max_per_occ: int = TOP_N_ELEMENTS) -> dict[str, list[str]]:
    """
    Parse Skills.txt (O*NET-SOC Code, Element Name, Scale ID IM/LV, Data Value).
    Returns SOC -> top max_per_occ skill names by importance (IM).
    """
    out: dict[str, dict[str, float]] = {}
    raw = skills_path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(StringIO(raw), delimiter="\t")
    for row in reader:
        code = (row.get("O*NET-SOC Code") or row.get("onet_soc_code") or row.get("code") or "").strip()
        name = (row.get("Element Name") or row.get("element_name") or row.get("Description") or "").strip()
        scale = (row.get("Scale ID") or "").strip().upper()
        try:
            val = float(row.get("Data Value") or row.get("data_value") or 0)
        except (TypeError, ValueError):
            continue
        if not code or not name:
            continue
        if code not in out:
            out[code] = {}
        if scale == "IM":
            out[code][name] = val
        elif scale == "LV" and name not in out[code]:
            out[code][name] = val
    result = {}
    for code, name_to_val in out.items():
        ordered = sorted(name_to_val.items(), key=lambda x: -x[1])
        result[code] = [n for n, _ in ordered[:max_per_occ]]
    return result


def _read_element_file(
    path: Path,
    max_per_occ: int = TOP_N_ELEMENTS,
    prefer_scale: str = "IM",
) -> dict[str, list[str]]:
    """
    Parse O*NET element file (Abilities, Knowledge, Work Activities): tab-delimited,
    columns O*NET-SOC Code, Element Name, Scale ID (IM/LV), Data Value.
    Returns SOC -> top max_per_occ names by importance (IM).
    """
    out: dict[str, dict[str, float]] = {}
    raw = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(StringIO(raw), delimiter="\t")
    for row in reader:
        code = (row.get("O*NET-SOC Code") or row.get("onet_soc_code") or row.get("code") or "").strip()
        name = (row.get("Element Name") or row.get("element_name") or "").strip()
        scale = (row.get("Scale ID") or "").strip().upper()
        try:
            val = float(row.get("Data Value") or row.get("data_value") or 0)
        except (TypeError, ValueError):
            continue
        if not code or not name:
            continue
        if code not in out:
            out[code] = {}
        if scale == prefer_scale:
            out[code][name] = val
        elif scale == "LV" and name not in out[code]:
            out[code][name] = val
    result = {}
    for code, name_to_val in out.items():
        ordered = sorted(name_to_val.items(), key=lambda x: -x[1])
        result[code] = [n for n, _ in ordered[:max_per_occ]]
    return result


def _read_interests(path: Path) -> dict[str, list[str]]:
    """
    Parse Interests.txt (RIASEC + OI scores). Returns SOC -> list of interest names ordered by score desc.
    Excludes metadata elements (e.g. First/Second/Third Interest High-Point) so only the 6 RIASEC dimensions are kept.
    """
    out: dict[str, list[tuple[str, float]]] = {}
    raw = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(StringIO(raw), delimiter="\t")
    for row in reader:
        code = (row.get("O*NET-SOC Code") or row.get("onet_soc_code") or row.get("code") or "").strip()
        name = (row.get("Element Name") or row.get("element_name") or "").strip()
        if "high-point" in name.lower():
            continue
        try:
            val = float(row.get("Data Value") or row.get("data_value") or 0)
        except (TypeError, ValueError):
            continue
        if not code or not name:
            continue
        out.setdefault(code, []).append((name, val))
    result = {}
    for code, pairs in out.items():
        ordered = sorted(pairs, key=lambda x: -x[1])
        result[code] = [n for n, _ in ordered]
    return result


def _read_job_zones(path: Path) -> dict[str, int]:
    """Parse Job Zones.txt; returns SOC -> job zone 1-5 (preparation level)."""
    out = {}
    raw = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(StringIO(raw), delimiter="\t")
    for row in reader:
        code = (row.get("O*NET-SOC Code") or row.get("onet_soc_code") or row.get("code") or "").strip()
        try:
            zone = int(float(row.get("Job Zone") or row.get("job_zone") or 0))
        except (TypeError, ValueError):
            continue
        if code and 1 <= zone <= 5:
            out[code] = zone
    return out


def process_onet_occupations_and_skills(
    onet_dir: Optional[Path] = None,
    onet_zip_url: str = ONET_TEXT_ZIP_URL,
) -> tuple[dict[str, str], dict[str, list[str]], bool, dict]:
    """
    Load O*NET occupation titles, skills, and optional content (abilities, knowledge, etc.) from data/onet/.
    If the required files are missing, downloads the O*NET text ZIP, extracts to data/onet/,
    then deletes the zip. Reads from the extracted files on disk.
    Returns:
        titles: dict mapping O*NET-SOC code (e.g. '15-1252.00') to title
        skills_by_occ: dict mapping O*NET-SOC code to list of skill description strings
        extracted_this_run: True if we just downloaded and extracted
        extras: dict with optional keys abilities, knowledge, work_activities (SOC -> list[str]),
                interests (SOC -> list[str]), job_zone (SOC -> int 1-5). Missing keys if file not found.
    """
    base = Path(__file__).resolve().parent.parent.parent
    onet_dir = onet_dir or base / "data" / "onet"

    occ_file = _find_file_in_dir(onet_dir, "Occupation Data.txt") or _find_file_in_dir(onet_dir, "occupation_data.txt")
    skills_file = _find_file_in_dir(onet_dir, "Skills.txt", exclude_containing="Technology")

    extracted_this_run = False
    if not occ_file or not skills_file:
        _download_and_extract_to(onet_zip_url, onet_dir)
        extracted_this_run = True
        occ_file = _find_file_in_dir(onet_dir, "Occupation Data.txt") or _find_file_in_dir(onet_dir, "occupation_data.txt")
        skills_file = _find_file_in_dir(onet_dir, "Skills.txt", exclude_containing="Technology")

    if not occ_file:
        raise RuntimeError("O*NET extract missing Occupation Data file. Check onetcenter.org and data/onet/.")
    if not skills_file:
        raise RuntimeError("O*NET extract missing Skills file. Check onetcenter.org and data/onet/.")

    titles = _read_occupation_data(occ_file)
    skills_by_occ = _read_skills(skills_file)

    if not titles:
        raise RuntimeError("O*NET Occupation Data file is empty or unreadable.")

    extras = {}
    for filename, key, reader in [
        ("Abilities.txt", "abilities", lambda p: _read_element_file(p)),
        ("Knowledge.txt", "knowledge", lambda p: _read_element_file(p)),
        ("Work Activities.txt", "work_activities", lambda p: _read_element_file(p)),
        ("Interests.txt", "interests", _read_interests),
        ("Job Zones.txt", "job_zone", _read_job_zones),
    ]:
        f = _find_file_in_dir(onet_dir, filename)
        if f:
            try:
                extras[key] = reader(f)
            except Exception:
                pass

    return titles, skills_by_occ, extracted_this_run, extras
