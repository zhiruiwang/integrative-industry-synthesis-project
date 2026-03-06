# Task 7: Mentor Presentation and Defense – 15-Minute Outline

Use this outline to prepare the final mentor presentation. 

---

## Required structure (cover all 7 sections; order may vary)

### 1. Industry Context and Problem Definition (~2 min)

- **Industry/sector:** Workforce Development / HR Technology / Education Technology
- **Real-world problem:** Workers lack visibility into career transitions, skills to develop, salary/automation tradeoffs; employers and policymakers lack transition-feasibility and skill-gap tools; job platforms often give generic advice
- **Why it matters:** Evidence-based, personalized pathways support workforce decisions and equity-informed intelligence
- **Why AI is appropriate:** Large-scale labor market data, skill similarity and ranking (ML/recommender), personalized roadmaps (agentic workflows)—spans statistics, ML, and agentic systems

**Purpose:** Ground the listener in real-world context before technical discussion.

---

### 2. Integrated AI System Overview (~2–3 min)

- **What the system does:** AI Career Pathway and Labor Market Intelligence Platform—Streamlit app where users enter current occupation in natural language and receive ranked career transitions plus a 6–12 month narrative roadmap
- **Major components:** Data pipeline (O*NET + BLS) → occupation dataset → occupation matcher agent → statistical engine → skill similarity & recommender (TF-IDF + weighted score) → roadmap generator agent → final report
- **How they interact:** Data flows in sequence; agents use tools to resolve input and produce roadmap; statistics feed the recommender; recommender feeds the roadmap agent
- **Use a diagram:** Point to or include the architecture diagram (e.g., from `docs/02_System_Design_and_Architecture.md`)

**Purpose:** Explain what the system does at a high level and how components interact.

---

### 3. Integration of Prior Capstone Projects (~2 min)

- **At least three prior capstones integrated:** This project integrates **four** in code (1, 2, 3, 6)
- **What each contributed:**
  - **Capstone 1 (AI Programming):** Reproducible data workflow—O*NET + BLS pipeline, `refresh-data` CLI
  - **Capstone 2 (Statistical Analysis):** Labor market stats—growth, salary, risk-adjusted opportunity scores
  - **Capstone 3 (Applied ML):** Skill similarity (TF-IDF/cosine) and recommender (0.8×overlap + 0.1×growth + 0.1×salary)
  - **Capstone 6 (Agentic AI):** Multi-agent system—occupation matcher agent, roadmap generator agent
- **Why combined:** Single pipeline from data → metrics → ranking → narrative output; each capstone contributes a defined output
- **How integration improved the solution:** End-to-end runnable artifact with clear handoffs; not a collection of disconnected parts

**Purpose:** Demonstrate synthesis across the program.

---

### 4. Key Technical Decisions and Tradeoffs (~2 min)

- **TF-IDF and cosine similarity** (not embeddings): Avoid external API dependency; interpretable; sufficient for demo—tradeoff: possible loss in accuracy vs. embeddings
- **Weighted score (overlap + growth + salary):** Transparent, tunable—tradeoff: fixed formula vs. learned model
- **ADK agents for occupation matching and roadmap:** Agentic orchestration with tools; no separate “generative” module—roadmap generator produces narrative when API key is set
- **Assumptions:** BLS/O*NET data available; transition “success” approximated by heuristics; users understand decision-support framing
- **Boundaries:** In scope—integrated demo and documentation; out of scope—real-time job feeds, legal/financial advice, outcome guarantees

**Purpose:** Show honest reasoning about why choices were made and what tradeoffs were accepted.

---

### 5. Ethical Considerations and Responsible AI (~2 min)

- **Bias and fairness:** Labor data can encode gender, racial, or educational inequities (O’Neil, 2016); unaudited models can reinforce disparities—safeguard: recommend bias auditing (e.g., disaggregated metrics) before real-world use
- **Transparency and overconfidence:** Users may treat probabilities as guarantees—safeguard: roadmap and UI state “decision support only,” report uncertainty
- **Accountability:** System framed as support, not replacement; disclaimers and limitation text in generated roadmap
- **Governance:** For real-world use—define accountability, retraining/audit cadence, user feedback loops
- **Automation displacement:** Roadmap and docs surface limitations so users interpret recommendations in context

**Purpose:** Ethical discussion must be specific to this system and industry, not generic.

---

### 6. Evaluation, Limitations, and Risks (~2 min)

- **How evaluated:** Qualitative—manual inspection of roadmap and ranking coherence (e.g., Web Developer → Computer and Information Research Scientists); execution—run Streamlit app for end-to-end verification
- **Goals met:** Pipeline produces metrics, rankings, skill gaps, and a structured roadmap
- **Strengths:** Coherent integration, observable outputs, reproducible (`requirements.txt`, modular code), interpretable scores
- **Limitations:** Heuristic-based transition scoring (no trained model); static O*NET/BLS snapshot; no real-time job-posting integration
- **Risks for production:** Bias propagation if data encode inequities; user over-reliance if probabilities misinterpreted; need real transition labels and larger taxonomy for deployment

**Purpose:** Show reflective judgment—what worked, what did not, what would need attention in production.

---

### 7. Professional Relevance and Next Steps (~1 min)

- **Readiness for real-world AI work:** Synthesizes data, ML, recommender, and agentic components; justifies design with prior work; addresses ethics in context; documents for reproducibility
- **Skills showcased:** Technical integration, analytical reasoning, ethical awareness, professional communication
- **Next steps / improvements:** Real transition labels and larger data; optional LLM roadmap with guardrails; fairness audits and user studies; formal quantitative evaluation (e.g., AUC on transition pairs)

**Purpose:** Connect the work to professional practice and continuous improvement.

---

## Preparing for the live defense (15 min after presentation)

- Be prepared to answer questions on: **design choices**, **integration strategy**, **ethical reasoning**, **limitations and risks**, **real-world deployment**
- Answers should be grounded in your **actual implementation, analysis, and paper**
- Demonstrate **reflective judgment**—what worked, what did not, what could be improved—rather than defensiveness
- *“If you can clearly explain why you built what you built, you are prepared.”*
