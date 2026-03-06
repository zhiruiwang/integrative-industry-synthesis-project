"""
Occupation matching agent (part of the multi-agent system).

Matches user natural-language occupation input (e.g. "software developer") to the closest
occupation in the dataset using an ADK agent with a tool that provides the occupation list.
Requires OPENAI_API_KEY and Google ADK (same as the career pathway agent).
"""
import asyncio
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# O*NET-SOC id pattern: XX-XXXX.XX
_SOC_ID_PATTERN = re.compile(r"\b(\d{2}-\d{4}\.\d{2})\b")

# Max occupations to send to the agent (context limit)
MAX_OCCUPATIONS_IN_PROMPT = 800


def _build_occupation_list_text(occupations: list[dict], max_items: int = MAX_OCCUPATIONS_IN_PROMPT) -> str:
    """One line per occupation: id  title."""
    subset = occupations[:max_items]
    lines = []
    for o in subset:
        oid = o.get("id") or ""
        title = (o.get("title") or "").strip()
        lines.append(f"{oid}  {title}")
    return "\n".join(lines)


async def _run_matcher_agent_async(query: str, occupations: list[dict]) -> Optional[str]:
    """
    Run the occupation-matching ADK agent. Returns the chosen occupation id string, or None.
    """
    if not occupations:
        return None
    try:
        from google.adk.agents import Agent
        from google.adk.models.lite_llm import LiteLlm
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
    except ImportError:
        return None

    occupation_list_text = _build_occupation_list_text(occupations)

    def get_occupation_list() -> str:
        """Return the list of occupations (id and title per line) for the agent to match against."""
        return occupation_list_text

    model_name = os.environ.get("LITELLM_MODEL", "openai/gpt-4o-mini")
    agent = Agent(
        name="occupation_matcher_agent",
        model=LiteLlm(model=model_name),
        description="Matches a user's free-text job description to the closest occupation from a standard list.",
        instruction=(
            "You are an occupation-matching assistant. The user will describe their current job in free text. "
            "Use the get_occupation_list tool to retrieve the list of occupations (each line is: id then title). "
            "Choose the ONE occupation that best matches the user's description. "
            "Reply with ONLY the occupation id (e.g. 15-1252.00), nothing else. Use the exact id from the list."
        ),
        tools=[get_occupation_list],
    )

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="career_pipeline",
        user_id="user_1",
        session_id="session_matcher",
    )
    runner = Runner(
        agent=agent,
        app_name="career_pipeline",
        session_service=session_service,
    )

    user_message = (
        f"User's current occupation (free text): \"{query}\". "
        "Which occupation from the list best matches? Reply with only the occupation id (e.g. 15-1252.00)."
    )
    content = types.Content(role="user", parts=[types.Part(text=user_message)])

    final_text = ""
    async for event in runner.run_async(
        user_id="user_1",
        session_id="session_matcher",
        new_message=content,
    ):
        if getattr(event, "is_final_response", lambda: False)():
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        final_text = part.text
                        break
            break

    if not final_text:
        return None
    match = _SOC_ID_PATTERN.search(final_text.strip())
    return match.group(1) if match else None


def match_occupation_by_agent(
    query: str,
    occupations: list[dict],
) -> Optional[tuple[dict, float]]:
    """
    Run the occupation-matching agent to resolve natural language to the closest occupation.
    Part of the multi-agent system (this agent runs before the career pathway agent).

    Returns (occupation, confidence) or None if API unavailable, query empty, or no match.
    """
    query = (query or "").strip()
    if not query or not occupations:
        return None
    if not os.environ.get("OPENAI_API_KEY"):
        return None

    coro = _run_matcher_agent_async(query, occupations)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        with ThreadPoolExecutor(max_workers=1) as pool:
            oid = pool.submit(asyncio.run, coro).result()
    else:
        oid = asyncio.run(coro)

    if not oid:
        return None
    for o in occupations:
        if o.get("id") == oid:
            return (o, 1.0)
    return None
