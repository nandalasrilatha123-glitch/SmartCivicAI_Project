"""
The actual LangGraph StateGraph implementing spec §9's workflow:

    classification_agent -> priority_agent -> routing_agent -> citizen_response_agent

Used only when AI_PROVIDER=anthropic and ANTHROPIC_API_KEY is set (checked
by app/ai/pipeline.py before this module is even imported). If `langgraph`
isn't installed, importing this module raises ImportError, which
pipeline.py catches to fall back to demo mode — consistent with every
other optional-dependency boundary in this project (see requirements-ai.txt).

Design note on the routing agent: unlike classification/priority/response,
routing here does NOT call the LLM. Picking a department for a module is a
deterministic database lookup (done by the caller, since LangGraph nodes
in this design are pure functions with no DB session of their own), not a
language-understanding task an LLM adds value to. It's still a distinct
node in the graph — matching the architecture in spec §9 — it just assigns
a confidence score to a decision that was already made before the graph
ran, rather than making the decision itself. This mirrors exactly what the
demo-mode pipeline does in app/ai/pipeline.py, so switching AI_PROVIDER
doesn't change *what* gets routed, only how classification/priority/
response are produced.
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai import llm_classifier
from app.core.enums import PriorityLevel


class AgentState(TypedDict, total=False):
    complaint_text: str
    language: str
    module_code: str
    module_label: str
    categories: list[dict]
    department_id: str | None
    department_name: str | None

    predicted_category_id: str | None
    category_confidence: float
    module_confidence: float

    priority: str
    priority_confidence: float
    priority_reasoning: str

    routing_confidence: float

    citizen_response: str


def _classification_node(state: AgentState) -> AgentState:
    result = llm_classifier.classify_complaint(state["complaint_text"], state["module_label"], state["categories"])
    return {
        "predicted_category_id": result["predicted_category_id"],
        "category_confidence": result["category_confidence"],
        "module_confidence": result["module_confidence"],
    }


def _priority_node(state: AgentState) -> AgentState:
    result = llm_classifier.assess_priority(state["complaint_text"])
    return {
        "priority": result["priority"].value,
        "priority_confidence": result["confidence"],
        "priority_reasoning": result["reasoning"],
    }


def _routing_node(state: AgentState) -> AgentState:
    # Deterministic — see module docstring. Confidence reflects whether a
    # department was actually resolvable for this module, not an LLM judgment.
    return {"routing_confidence": 0.9 if state.get("department_id") else 0.0}


def _citizen_response_node(state: AgentState) -> AgentState:
    message = llm_classifier.generate_citizen_response(
        state["complaint_text"],
        state["module_label"],
        state["priority"],
        state.get("department_name") or "the relevant department",
        state["language"],
    )
    return {"citizen_response": message}


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classification_agent", _classification_node)
    graph.add_node("priority_agent", _priority_node)
    graph.add_node("routing_agent", _routing_node)
    graph.add_node("citizen_response_agent", _citizen_response_node)

    graph.add_edge(START, "classification_agent")
    graph.add_edge("classification_agent", "priority_agent")
    graph.add_edge("priority_agent", "routing_agent")
    graph.add_edge("routing_agent", "citizen_response_agent")
    graph.add_edge("citizen_response_agent", END)

    return graph.compile()


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


def run_langgraph_pipeline(
    *,
    complaint_text: str,
    language: str,
    module_code: str,
    module_label: str,
    categories: list[dict],
    department_id: str | None,
    department_name: str | None,
) -> dict:
    """
    Runs the full 4-agent graph. Raises llm_classifier.LLMCallError (via
    whichever node fails first) if any stage's API call or response
    parsing fails — the whole run is treated as a single unit so a partial
    LLM result never gets silently mixed with demo-mode data.
    """
    initial_state: AgentState = {
        "complaint_text": complaint_text,
        "language": language,
        "module_code": module_code,
        "module_label": module_label,
        "categories": categories,
        "department_id": department_id,
        "department_name": department_name,
    }

    final_state = _get_graph().invoke(initial_state)

    return {
        "predicted_category_id": final_state.get("predicted_category_id"),
        "category_confidence": final_state["category_confidence"],
        "module_confidence": final_state["module_confidence"],
        "priority": PriorityLevel(final_state["priority"]),
        "priority_confidence": final_state["priority_confidence"],
        "priority_reasoning": final_state["priority_reasoning"],
        "routing_confidence": final_state["routing_confidence"],
        "citizen_response": final_state["citizen_response"],
    }
