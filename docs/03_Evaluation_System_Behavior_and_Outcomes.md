# Task 5: Evaluation of System Behavior and Outcomes

## Intended Goals
- Produce labor market metrics (growth, salary, risk-adjusted scores) per occupation.
- Rank transitions by a combined score (profile overlap 80%, growth 10%, salary 10%) and identify skill, knowledge, and ability gaps.
- Generate a structured, human-readable career roadmap via the roadmap generator agent.

## Strengths
- **Integration:** Statistics, skill similarity (TF-IDF), recommender, and multi-agent system (occupation matcher + roadmap generator) run in a single pipeline.
- **Observable outputs:** The system produces a full report (roadmap), ranked transition table with gaps. Streamlit UI and CLI both produce visible results.
- **Reproducibility:** Deterministic logic; `requirements.txt` and clear modules support reproduction.
- **Interpretability:** Profile overlap, growth, salary delta, and skill/knowledge/ability gaps are exposed; roadmap explains limitations.

## Limitations and Failure Cases
- **Scoring:** Transition “success” is heuristic-based (skill overlap + salary delta). Real deployment could use labeled transition data; ranking uses a fixed formula (overlap + growth + salary), not a trained model.
- **Static data:** Occupation set is from O*NET/BLS snapshot; no real-time BLS or job-posting integration.
- **Bias:** If historical data encode wage gaps or underrepresentation, model outputs can perpetuate inequities.

## Tradeoffs Assessed
- **Performance vs. complexity:** TF-IDF and a simple weighted score (overlap + growth + salary) were chosen so the pipeline runs quickly and remains interpretable; more complex models could improve accuracy at the cost of explainability.
- **Realism vs. scope:** Using a small sample keeps the artifact deliverable; production would require larger datasets and validation.
- **Responsible use:** Outputs are framed as decision support, with explicit disclaimers and risk/limitation text in the roadmap.

## How Evaluation Was Conducted
- **Qualitative:** Manual inspection of roadmap content and ranking coherence (e.g., Web Developer → Computer and Information Research Scientists as a top transition).
- **Execution:** Run `streamlit run app.py` to verify end-to-end outputs.

