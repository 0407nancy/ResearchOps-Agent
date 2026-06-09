from __future__ import annotations

from langchain.tools import tool

from deerflow.researchops.intent import classify_intent


@tool("classify_research_intent", parse_docstring=True)
def classify_research_intent_tool(user_input: str) -> str:
    """Classify a ResearchOps user request and extract slots as JSON.

    Args:
        user_input: Raw user request to classify.
    """
    return classify_intent(user_input).model_dump_json(indent=2)
