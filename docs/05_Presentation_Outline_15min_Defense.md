# Task 7: Mentor Presentation and Defense – 15-Minute Outline

Use this outline to prepare the final mentor presentation. 

---

## 1. Industry problem and motivation (2–3 min)

- **Industry:** Workforce Development / HR Tech / Education Technology
- **Problem:** Workers lack visibility into career transitions, skills to develop, and salary/automation tradeoffs; employers and policymakers lack transition-feasibility and skill-gap tools; job platforms often give generic advice
- **Why AI:** Large-scale data, prediction, similarity/recommendation, personalized narrative, and agentic orchestration—naturally spans statistics, ML, deep learning, generative AI, and agentic systems
- **Constraint:** System is decision support, not replacement for human judgment

---

## 2. System design and integration choices (4–5 min)

- **High-level flow:** Data pipeline (Capstone 1) → Occupation data → User profile → Statistical engine → Skill similarity & recommender (TF-IDF + score) → Agentic agents → Report
- **Integration of prior projects:**
  - Capstone 1: Reproducible data workflow (O*NET + BLS pipeline)
  - Capstone 2: Labor market stats (growth, salary, risk-adjusted scores)
  - Capstone 3: Skill similarity (TF-IDF/cosine) and recommender (overlap + growth + salary score)
  - Capstone 6: Multi-agent system (occupation matcher agent, roadmap generator agent)
- **Key design choices:** TF-IDF for reproducibility, weighted score for ranking, template or LLM roadmap, ADK agents for occupation matching
- **Architecture diagram:** Point to `docs/02_System_Design_and_Architecture.md` (and/or include slide with Mermaid/text diagram)

---

## 3. Ethical considerations and safeguards (2–3 min)

- **Bias/fairness:** Labor data can encode historical inequities; need bias auditing (e.g., by demographic group) before real-world use
- **Transparency/overconfidence:** Probabilities are model-based estimates; roadmap states limitations and "decision support only"
- **Automation displacement:** Documentation and roadmap surface limitations so users interpret recommendations in context
- **Safeguards:** Clear disclaimers, uncertainty reporting, documentation of data and labels, governance considerations for deployment

---

## 4. Evaluation results and limitations (2–3 min)

- **Goals met:** Pipeline produces metrics, rankings, skill gaps, and a structured roadmap
- **Strengths:** Coherent integration, observable outputs, reproducible (requirements.txt, modular code)
- **Limitations:** Heuristic-based label, small static sample
- **Tradeoffs:** Interpretability vs. performance, realism vs. scope; chosen to favor runnable, defensible artifact

---

## 5. Professional relevance and next steps (1–2 min)

- **Portfolio value:** Demonstrates system-level thinking, cross-domain integration, and industry relevance
- **Readiness:** Justifies design with prior work, addresses ethics in context, documents for reproducibility
- **Next steps:** Real labels and larger data, optional LLM roadmap with guardrails, fairness audits, user studies

---

## Defense preparation

- Be ready to **defend**: why these components (and at least three prior capstones), why TF-IDF over embeddings, how the combined score (overlap + growth + salary) ranks transitions, how the multi-agent system (occupation matcher, roadmap generator) produces the roadmap
- Be ready to **explain**: how each prior capstone informed the design (reference the Integration Plan and paper)
- Be ready to **discuss**: specific ethical risks for workforce/career systems and how your safeguards address them
