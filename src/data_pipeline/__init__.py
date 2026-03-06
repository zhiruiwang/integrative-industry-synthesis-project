"""
Data pipeline: O*NET + BLS (OES wages, employment projections); merge to data/occupations.csv.
Orchestration and CLI: src.run_data_pipeline (run_data_pipeline, refresh-data).
"""
from .process_bls_oes import process_bls_oes_wages
from .process_bls_projections import process_bls_projections_growth
from .process_onet import process_onet_occupations_and_skills
from .merge import merge_occupations
from .soc import normalize_soc

__all__ = [
    "process_bls_oes_wages",
    "process_bls_projections_growth",
    "process_onet_occupations_and_skills",
    "merge_occupations",
    "normalize_soc",
]

