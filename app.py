"""
Streamlit UI for the Career Pathway system.

User enters current occupation (natural language or SOC code) and optionally
multi-selects core skills, abilities, and knowledge. Recommendations use both
the matched occupation and the selected profile to rank transition options.
"""
import html
import os
import sys
from pathlib import Path
from typing import Optional

# Run from project root so src and data are available
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.data_loader import load_occupations
from src.statistical_engine import compute_labor_market_metrics
from src.recommender import (
    build_skill_similarity_matrix,
    recommend_transitions,
    compute_similarity_of_text_to_occupations,
)
from src.occupation_matcher import match_occupation_by_agent
from src.roadmap_generator import generate_roadmap


def _inject_css():
    st.markdown(
        """
        <style>
        [data-testid="stVerticalBlock"] > div:has([data-testid="stVerticalBlock"]) {
            border-radius: 0.5rem;
        }
        /* Left column: white sidebar panel */
        [data-testid="stHorizontalBlock"] > div:first-child {
            background: #ffffff;
            padding: 1.25rem;
            border-radius: 0.5rem;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        /* Right column: light grey content area */
        [data-testid="stHorizontalBlock"] > div:last-child {
            background: #f5f7fa;
            padding: 1.25rem;
            border-radius: 0.5rem;
            min-height: 400px;
        }
        .placeholder-box {
            background: #ffffff;
            border: 2px dashed #d1d5db;
            border-radius: 0.5rem;
            padding: 3rem 2rem;
            text-align: center;
            color: #6b7280;
        }
        .occ-summary { margin: 0.5rem 0 1rem 0; font-size: 0.9rem; }
        .occ-summary .occ-stats { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.75rem; }
        .occ-summary .occ-metric {
            flex: 1;
            min-width: 0;
            min-height: 4rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 0.65rem 0.9rem;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .occ-summary .occ-metric-label { font-size: 0.85rem; color: #6b7280; font-weight: 500; margin-bottom: 0.25rem; }
        .occ-summary .occ-metric-value { font-size: 1.35rem; font-weight: 600; color: #111827; }
        .occ-summary .occ-cards { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 0.25rem; }
        .occ-summary .occ-card {
            flex: 1;
            min-width: 0;
            min-height: 4rem;
            padding: 0.6rem 0.75rem;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .occ-summary .occ-card .occ-card-label { font-size: 0.8rem; font-weight: 600; color: #374151; margin-bottom: 0.35rem; display: block; }
        .occ-summary .occ-tags { display: flex; flex-wrap: wrap; gap: 0.25rem; }
        .occ-summary .tag { display: inline-block; padding: 0.2rem 0.45rem; border-radius: 0.35rem; font-size: 0.75rem; }
        .occ-summary .tag.skill { background: #e0e7ff; color: #3730a3; }
        .occ-summary .tag.ability { background: #d1fae5; color: #065f46; }
        .occ-summary .tag.knowledge { background: #fef3c7; color: #92400e; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _parse_csv_list(s: str) -> list[str]:
    """Split comma-separated values and return sorted unique non-empty strings."""
    if not s or not isinstance(s, str):
        return []
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return sorted(set(parts))


@st.cache_data
def _load_data():
    """Load occupations and build option lists and matrices. Expects to run from project root."""
    occupations = load_occupations(data_dir="data")
    stats = compute_labor_market_metrics(occupations)
    skill_matrix, vectorizer = build_skill_similarity_matrix(occupations)

    skills = []
    abilities = []
    knowledge = []
    for o in occupations:
        skills.extend(_parse_csv_list(o.get("skills") or ""))
        abilities.extend(_parse_csv_list(o.get("abilities") or ""))
        knowledge.extend(_parse_csv_list(o.get("knowledge") or ""))

    options = {
        "skills": sorted(set(skills)),
        "abilities": sorted(set(abilities)),
        "knowledge": sorted(set(knowledge)),
    }
    return occupations, stats, skill_matrix, vectorizer, options


def _resolve_occupation(query: str, occupations: list) -> Optional[dict]:
    """Resolve occupation from natural language via the occupation-matching agent. Returns None on failure."""
    query = (query or "").strip()
    if not query:
        return None
    matched = match_occupation_by_agent(query, occupations)
    if matched is None:
        return None
    return matched[0]


def main():
    st.set_page_config(
        page_title="Career Pathway",
        page_icon="📋",
        layout="wide",
    )
    _inject_css()

    if "selected_skills" not in st.session_state:
        st.session_state["selected_skills"] = []
    if "selected_abilities" not in st.session_state:
        st.session_state["selected_abilities"] = []
    if "selected_knowledge" not in st.session_state:
        st.session_state["selected_knowledge"] = []

    st.title("Career Pathway & Transition Intelligence Platform")
    st.markdown(
        "Enter your **current occupation** and refine your profile. Results appear on the right."
    )

    try:
        occupations, stats, skill_matrix, vectorizer, options = _load_data()
    except FileNotFoundError as e:
        st.error(
            "Occupation data not found. Run from project root: `python -m src.run_data_pipeline refresh-data`"
        )
        st.stop()

    col_left, col_right = st.columns([1, 2])

    with col_left:
        occupation_query = st.text_input(
            "Current occupation",
            value="",
            placeholder="e.g. web developer, nurse",
            help="Describe your current job in natural language.",
        )
        st.subheader("Refine your profile (optional)")
        selected_skills = st.multiselect(
            "Skills",
            options=options["skills"],
            default=st.session_state["selected_skills"],
            max_selections=20,
            help="Select your core skills.",
        )
        selected_abilities = st.multiselect(
            "Abilities",
            options=options["abilities"],
            default=st.session_state["selected_abilities"],
            max_selections=20,
            help="Select your core abilities.",
        )
        selected_knowledge = st.multiselect(
            "Knowledge",
            options=options["knowledge"],
            default=st.session_state["selected_knowledge"],
            max_selections=20,
            help="Select your knowledge areas.",
        )
        st.session_state["selected_skills"] = selected_skills
        st.session_state["selected_abilities"] = selected_abilities
        st.session_state["selected_knowledge"] = selected_knowledge

        get_recs = st.button("Get recommendations", type="primary")
        if st.button("Clear selections", type="secondary"):
            st.session_state["selected_skills"] = []
            st.session_state["selected_abilities"] = []
            st.session_state["selected_knowledge"] = []
            st.rerun()

    with col_right:
        if get_recs:
            if not os.environ.get("OPENAI_API_KEY"):
                st.error(
                    "**OPENAI_API_KEY is required.** Set it in a `.env` file (e.g. `OPENAI_API_KEY=sk-...`) and restart the app. "
                    "Occupation matching and roadmap generation both require an API key; the app does not run without it."
                )
            elif not occupation_query.strip():
                st.warning("Please enter your current occupation.")
            else:
                with st.spinner("Matching your occupation..."):
                    current_occ = _resolve_occupation(occupation_query, occupations)
                if current_occ is None:
                    st.error("Could not match that occupation. Try a different phrase (e.g. 'web developer', 'nurse').")
                else:
                    parts = [current_occ.get("title") or "", current_occ.get("id") or ""]
                    if selected_skills:
                        parts.append(" ".join(selected_skills))
                    if selected_abilities:
                        parts.append(" ".join(selected_abilities))
                    if selected_knowledge:
                        parts.append(" ".join(selected_knowledge))
                    augmented_text = " ".join(p for p in parts if p).strip()

                    with st.spinner("Computing recommendations..."):
                        curr_idx = next(i for i, o in enumerate(occupations) if o["id"] == current_occ["id"])
                        if augmented_text:
                            sim_row = compute_similarity_of_text_to_occupations(
                                augmented_text, occupations, vectorizer
                            )
                            skill_matrix_enhanced = skill_matrix.copy()
                            skill_matrix_enhanced[curr_idx, :] = sim_row
                        else:
                            skill_matrix_enhanced = skill_matrix

                        ranked = recommend_transitions(
                            current_occ, occupations, skill_matrix_enhanced, stats, top_k=10
                        )

                    st.session_state["career_result"] = {
                        "current_occ": current_occ,
                        "ranked": ranked,
                    }
                    st.rerun()
        elif "career_result" in st.session_state:
            current_occ = st.session_state["career_result"]["current_occ"]
            ranked = st.session_state["career_result"]["ranked"]
            st.success(f"Your current occupation is matched to: **{current_occ.get('title') or 'N/A'}** ({current_occ.get('id')})")
            sal = current_occ.get("median_salary") or 0
            gr = current_occ.get("growth_pct")
            skills_list = _parse_csv_list(current_occ.get("skills") or "")
            abilities_list = _parse_csv_list(current_occ.get("abilities") or "")
            knowledge_list = _parse_csv_list(current_occ.get("knowledge") or "")
            n_show = 10
            def _tag_spans(items: list, css_class: str) -> str:
                if not items:
                    return ""
                subset = items[:n_show]
                extra = len(items) - n_show
                tags = "".join(f'<span class="tag {css_class}">{html.escape(s)}</span>' for s in subset)
                if extra > 0:
                    tags += f'<span class="tag {css_class}">+{extra} more</span>'
                return tags
            sal_display = f"${sal:,}" if sal else "N/A"
            gr_display = f"{gr}%" if gr is not None else "N/A"
            stats_html = (
                f'<div class="occ-metric">'
                f'<span class="occ-metric-label">Median salary</span>'
                f'<span class="occ-metric-value">{html.escape(sal_display)}</span>'
                f'</div>'
                f'<div class="occ-metric">'
                f'<span class="occ-metric-label">Job growth (next 10 yr)</span>'
                f'<span class="occ-metric-value">{html.escape(gr_display)}</span>'
                f'</div>'
            )
            cards_html = (
                f'<div class="occ-card"><span class="occ-card-label">Skills (top 7)</span><div class="occ-tags">{_tag_spans(skills_list, "skill") or "—"}</div></div>'
                f'<div class="occ-card"><span class="occ-card-label">Abilities (top 7)</span><div class="occ-tags">{_tag_spans(abilities_list, "ability") or "—"}</div></div>'
                f'<div class="occ-card"><span class="occ-card-label">Knowledge (top 7)</span><div class="occ-tags">{_tag_spans(knowledge_list, "knowledge") or "—"}</div></div>'
            )
            parts = [f'<div class="occ-summary"><div class="occ-stats">{stats_html}</div><div class="occ-cards">{cards_html}</div></div>']
            st.markdown("".join(parts), unsafe_allow_html=True)
            st.subheader("Top transition options")
            rows = []
            for i, rec in enumerate(ranked, 1):
                t = rec["target"]
                gr = t.get("growth_pct")
                rows.append({
                    "Rank": i,
                    "Target role": t.get("title") or "N/A",
                    "Profile overlap": f"{rec['skill_overlap']:.1%}",
                    "Median salary": f"${t.get('median_salary') or 0:,}",
                    "Salary vs current": f"{rec.get('salary_delta', 0):+,}",
                    "Job growth (next 10 yr)": f"{gr}%" if gr is not None else "N/A",
                    "Skill gaps": ", ".join(rec.get("skill_gaps", [])[:4]),
                    "Knowledge gaps": ", ".join(rec.get("knowledge_gaps", [])[:4]),
                    "Ability gaps": ", ".join(rec.get("ability_gaps", [])[:4]),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            with st.expander("View full career roadmap (6–12 month plan)", expanded=True):
                if "roadmap" not in st.session_state["career_result"]:
                    with st.spinner("Generating your 6–12 month career roadmap… this may take up to 30 seconds."):
                        report = generate_roadmap(current_occ, ranked[:5])
                        st.session_state["career_result"]["roadmap"] = report
                st.markdown(st.session_state["career_result"]["roadmap"])
            st.caption(
                "Recommendations are decision support only. Salary and growth figures are from BLS/O*NET and may vary by region."
            )
        else:
            st.markdown(
                '<div class="placeholder-box">'
                "<p><strong>No results yet</strong></p>"
                "<p>Enter your current occupation on the left and click <strong>Get recommendations</strong> to see transition options here.</p>"
                "</div>",
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
