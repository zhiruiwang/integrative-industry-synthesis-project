"""
Roadmap generator agent (part of the multi-agent system, Capstone 6).

Produces a personalized career roadmap via an ADK agent with a tool that provides
current role and top-transition context; the agent writes the narrative.
Requires OPENAI_API_KEY and Google ADK (same as the occupation matcher agent).
Raises if the key is missing or the agent/LLM call fails.
"""
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _build_roadmap_context(current_occ: dict, top_transitions: list[dict]) -> str:
    """Build the context text passed to the roadmap agent (current role + top transitions)."""
    current_sal = current_occ.get("median_salary", 0) or 0
    transitions_text = []
    for i, rec in enumerate(top_transitions[:5], 1):
        t = rec["target"]
        sal = t.get("median_salary", 0) or 0
        delta = rec.get("salary_delta", sal - current_sal)
        parts = [f"{i}. {t.get('title') or 'N/A'}:"]
        parts.append(f" profile overlap {rec.get('skill_overlap', 0):.1%};")
        gr = t.get("growth_pct")
        parts.append(
            f" salary ${sal:,} ({delta:+,} vs current), employment growth (next 10 yr) {f'{gr}%' if gr is not None else 'N/A'}. Skill gaps: {', '.join(rec.get('skill_gaps', [])[:6])}"
        )
        kg = rec.get("knowledge_gaps", [])[:4]
        if kg:
            parts.append(f" Knowledge gaps: {', '.join(kg)}.")
        ab = rec.get("ability_gaps", [])[:4]
        if ab:
            parts.append(f" Ability gaps: {', '.join(ab)}.")
        ig = rec.get("interest_gaps", [])[:4]
        if ig:
            parts.append(f" Interest gaps (to explore): {', '.join(ig)}.")
        if t.get("abilities"):
            parts.append(f" Abilities: {(str(t.get('abilities'))[:120])}.")
        if t.get("interests"):
            parts.append(f" Interests: {(str(t.get('interests'))[:120])}.")
        transitions_text.append(" ".join(parts))

    current_extra = []
    if current_occ.get("abilities"):
        current_extra.append(f"Abilities: {str(current_occ.get('abilities'))[:150]}")
    if current_occ.get("interests"):
        current_extra.append(f"Interests: {str(current_occ.get('interests'))[:150]}")
    current_extra_str = " ".join(current_extra) if current_extra else ""

    return (
        f"Current role: {current_occ.get('title') or 'N/A'} (SOC {current_occ.get('id', '')}), "
        f"salary ${current_sal:,}. {current_extra_str}\n\n"
        "Top recommended transitions (data):\n" + "\n".join(transitions_text)
    )


async def _run_roadmap_agent_async(context: str) -> str:
    """
    Run the roadmap-generator ADK agent. Returns the generated roadmap markdown.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is required for roadmap generation. Set it in .env (and OPENAI_BASE_URL if using a custom endpoint)."
        )
    try:
        from google.adk.agents import Agent
        from google.adk.models.lite_llm import LiteLlm
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
    except ImportError as e:
        raise RuntimeError(
            "Google ADK is required for the roadmap agent. Install: pip install google-adk"
        ) from e

    def get_roadmap_context() -> str:
        """Return the current role and top transition options for the agent to use when writing the roadmap."""
        return context

    model_name = os.environ.get("LITELLM_MODEL", "openai/gpt-4o-mini")
    agent = Agent(
        name="roadmap_generator_agent",
        model=LiteLlm(model=model_name),
        description="Generates a personalized markdown career roadmap from current role and top transition options.",
        instruction=(
            "You are a career coach. Use the get_roadmap_context tool to retrieve the current role and top transition options "
            "(with profile overlap, salary, employment growth, and skill/knowledge/ability/interest gaps). "
            "Then write a clear, personalized markdown career roadmap. "
            "Include: a short summary, then for each top transition a section with title, key metrics, suggested "
            "skill, knowledge, ability, and interest gaps where provided, and a brief 6–12 month phased plan. End with a short risk/limitations paragraph. "
            "Use markdown headers (##, ###) and bullet points. Be concise and actionable. Output only the roadmap markdown, no preamble."
        ),
        tools=[get_roadmap_context],
    )

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="career_pipeline",
        user_id="user_1",
        session_id="session_roadmap",
    )
    runner = Runner(
        agent=agent,
        app_name="career_pipeline",
        session_service=session_service,
    )

    user_message = (
        "Use get_roadmap_context to get the current role and top transition data, then write the full career roadmap in markdown."
    )
    content = types.Content(role="user", parts=[types.Part(text=user_message)])

    final_text = ""
    async for event in runner.run_async(
        user_id="user_1",
        session_id="session_roadmap",
        new_message=content,
    ):
        if getattr(event, "is_final_response", lambda: False)():
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        final_text = part.text
                        break
            break

    if not final_text or not final_text.strip():
        raise RuntimeError("Roadmap agent returned no content.")
    return final_text.strip()


def generate_roadmap(
    current_occ: dict,
    top_transitions: list[dict],
) -> str:
    """
    Generate a 6–12 month personalized career roadmap via the roadmap-generator ADK agent.
    Part of the multi-agent system (Capstone 6); no standalone Capstone 5 component.

    Requires OPENAI_API_KEY. Raises RuntimeError if the key is missing or the agent fails.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is required for roadmap generation. Set it in .env (and OPENAI_BASE_URL if using a custom endpoint)."
        )

    context = _build_roadmap_context(current_occ, top_transitions)
    coro = _run_roadmap_agent_async(context)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)
