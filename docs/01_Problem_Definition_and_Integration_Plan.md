# Task 1 & 2: Industry, Problem Definition, and Integration Plan

## Task 1 – Select an Industry and Define the Problem Space

### Industry
**Workforce Development / HR Technology / Education Technology**

### Industry Context and Problem
Workers often lack clear visibility into viable career transitions, including which skills to develop, potential salary trade-offs, and exposure to automation risk. At the same time, employers and policymakers lack robust insights into transition feasibility, equity-informed workforce intelligence, and forward-looking skill-gap forecasting. Existing job platforms typically offer generic recommendations, falling short of delivering evidence-based, personalized career pathways.

### Why This Problem Is Appropriate for AI
- **Large-scale labor market data** requires statistical and analytical methods.
- **Skill similarity and ranking** benefit from machine learning and recommender techniques.
- **Personalized roadmaps** and explanations suit generative AI and agentic workflows.


### Constraints, Risks, and Ethical Considerations
- Data is typically static (e.g., BLS, O*NET), not real-time job postings.
- Transition recommendations may be derived from heuristics.
- Historical labor market inequities (e.g., wage gaps) can be reflected in models.
- Labor market dynamics are inherently uncertain due to macroeconomic shifts, technological disruption, policy changes, and regional variability.
- System should support, not replace, human decision-making; probabilities are not guarantees.


---

## Task 2 – Define the Integration Plan

This project integrates **four** prior capstone projects domains (1, 2, 3, 6).

| Prior Capstone | Domain | What It Contributes | How It Interacts |
|----------------|--------|---------------------|------------------|
| **Capstone 1** | AI Programming Foundations | Reproducible data workflow: O*NET fetch, BLS merge, and pipeline orchestration (`src/data_pipeline/`, `src/run_data_pipeline.py` with `refresh-data`). Versioned inputs, deterministic merge, and documented steps for reproducible occupation data. | Produces the occupation dataset consumed by statistics, recommender, and agents; run via `python -m src.run_data_pipeline refresh-data` or on first load when data is missing. |
| **Capstone 2** | Statistical Analysis | Labor market analysis: salary distributions, growth trends. Outputs: growth score per occupation, salary percentiles, risk-adjusted opportunity score. | Feeds the recommender with growth and salary metrics; defines high-value targets. |
| **Capstone 3** | Applied ML | Transition scoring and skill similarity: a single heuristic score (0.8×overlap + 0.1×growth + 0.1×salary) ranks transitions; overlap via TF-IDF + cosine similarity over occupation text (skills, abilities, knowledge). | Consumes statistical outputs; produces ranked transitions and skill/knowledge/ability gaps for the agentic workflow. |
| **Capstone 6** | Agentic AI | **Multi-agent system (two ADK agents):** (1) **Occupation matcher agent**—resolves natural-language occupation; (2) **Roadmap generator agent**—uses a tool to get current role and top-transition context, then produces the markdown roadmap. | Occupation matcher runs first; app then runs recommender; roadmap generator agent produces the final report. |

### Component Interaction Summary
1. **Data pipeline** builds the occupation dataset from O*NET and BLS (fetch, merge, write to `data/`); reproducible via CLI and documented in the project README (Data pipeline section).
2. **User profile** and target preferences enter via the Streamlit app; natural-language occupation is resolved by the **occupation matcher agent**.
3. **Statistical engine** produces labor market metrics (growth, salary, risk-adjusted scores) from BLS/O*NET–derived data.
4. **Skill similarity & recommender** compute TF-IDF overlap and rank transitions by 0.8×overlap + 0.1×growth + 0.1×salary; output skill, knowledge, and ability gaps. 
5. **Multi-agent system:** **Occupation matcher agent** and **roadmap generator agent**. The roadmap agent has a tool that returns current role + top-transition context; the agent writes the markdown roadmap. 
6. **Final report** is the output of the **roadmap generator agent**.

This integration plan guides the system design (Task 3) and implementation (Task 4).
