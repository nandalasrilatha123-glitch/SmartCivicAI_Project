"""
Individual Anthropic LLM calls backing the real (non-demo) AI pipeline.

Each function is self-contained: it builds a prompt, calls the model,
parses strict JSON out of the response, and validates the result against
the enums/categories it was given. Any failure — network error, timeout,
malformed JSON, a value outside the allowed set — raises LLMCallError.
Callers (langgraph_pipeline.py) catch this and the whole request falls
back to the demo rule-based classifier (app/ai/demo_classifier.py), so a
flaky API key or rate limit never breaks complaint submission.

The `anthropic` package is imported lazily inside each function, not at
module load time, so this file can be imported even when requirements-ai.txt
hasn't been installed — app/ai/pipeline.py only reaches into this module
when AI_PROVIDER=anthropic AND ANTHROPIC_API_KEY is set, but the lazy
import is a second line of defense per spec §23/§27.
"""
from __future__ import annotations

import json
import re

from app.core.config import settings
from app.core.enums import PriorityLevel


class LLMCallError(Exception):
    """Raised on any failure calling or parsing an LLM response — always caught upstream."""


def _extract_json(text: str) -> dict:
    """Strips markdown code fences if present and parses the first JSON object found."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMCallError(f"Model did not return valid JSON: {exc}") from exc


def _call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
    try:
        import anthropic
    except ImportError as exc:
        raise LLMCallError("anthropic package not installed (see requirements-ai.txt)") from exc

    if not settings.ANTHROPIC_API_KEY:
        raise LLMCallError("ANTHROPIC_API_KEY is not configured")

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=settings.AI_MODEL_NAME,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=15.0,
        )
        return "".join(block.text for block in response.content if block.type == "text")
    except LLMCallError:
        raise
    except Exception as exc:  # noqa: BLE001 — any SDK/network error should trigger fallback, not crash
        raise LLMCallError(f"Anthropic API call failed: {exc}") from exc


def classify_complaint(complaint_text: str, module_label: str, categories: list[dict]) -> dict:
    """
    categories: [{"id": "...", "name_en": "..."}]
    Returns: {"predicted_category_id": str|None, "category_confidence": float, "module_confidence": float}
    """
    category_list = "\n".join(f'- id="{c["id"]}": {c["name_en"]}' for c in categories) or "(no categories configured)"

    system_prompt = (
        "You are a classification agent for a government civic-complaint system. "
        "You must choose the single best-matching category id from the provided list, or null if none fit well. "
        'Respond with ONLY a JSON object: {"predicted_category_id": "<id or null>", '
        '"category_confidence": <0.0-1.0>, "module_confidence": <0.0-1.0>}. No other text.'
    )
    user_prompt = (
        f"Module: {module_label}\n\nAvailable categories:\n{category_list}\n\n"
        f'Citizen complaint text: "{complaint_text}"'
    )

    raw = _call_claude(system_prompt, user_prompt)
    data = _extract_json(raw)

    valid_ids = {c["id"] for c in categories}
    predicted_id = data.get("predicted_category_id")
    if predicted_id is not None and predicted_id not in valid_ids:
        predicted_id = None

    try:
        category_confidence = float(data["category_confidence"])
        module_confidence = float(data["module_confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LLMCallError(f"Missing/invalid confidence fields in classification response: {data}") from exc

    return {
        "predicted_category_id": predicted_id,
        "category_confidence": max(0.0, min(1.0, category_confidence)),
        "module_confidence": max(0.0, min(1.0, module_confidence)),
    }


def assess_priority(complaint_text: str) -> dict:
    """Returns: {"priority": "LOW|MEDIUM|HIGH|CRITICAL", "confidence": float, "reasoning": str}"""
    system_prompt = (
        "You are a priority-assessment agent for a government civic-complaint system. "
        "Assess urgency based on safety risk, number of people affected, and how long the issue has persisted. "
        'Respond with ONLY a JSON object: {"priority": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL", '
        '"confidence": <0.0-1.0>, "reasoning": "<one short sentence>"}. No other text.'
    )
    user_prompt = f'Citizen complaint text: "{complaint_text}"'

    raw = _call_claude(system_prompt, user_prompt, max_tokens=256)
    data = _extract_json(raw)

    priority_str = str(data.get("priority", "")).upper()
    if priority_str not in PriorityLevel.__members__:
        raise LLMCallError(f"Model returned an invalid priority value: {data.get('priority')!r}")

    try:
        confidence = float(data["confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LLMCallError(f"Missing/invalid confidence in priority response: {data}") from exc

    return {
        "priority": PriorityLevel[priority_str],
        "confidence": max(0.0, min(1.0, confidence)),
        "reasoning": str(data.get("reasoning", ""))[:500],
    }


def generate_citizen_response(complaint_text: str, module_label: str, priority: str, department_name: str, language: str) -> str:
    """Returns a short acknowledgment message written directly in the citizen's own language."""
    language_name = {"en": "English", "te": "Telugu", "hi": "Hindi"}.get(language, "English")

    system_prompt = (
        "You are a citizen-response agent for a government civic-complaint platform. "
        f"Write a short (2-3 sentence), warm, professional acknowledgment message in {language_name}, "
        "in that language's native script. Mention the module, priority, and that it has been routed to "
        "the relevant department. Respond with ONLY the message text, no JSON, no quotes, no preamble."
    )
    user_prompt = (
        f"Module: {module_label}\nPriority: {priority}\nRouted to: {department_name}\n"
        f'Citizen complaint: "{complaint_text}"'
    )

    raw = _call_claude(system_prompt, user_prompt, max_tokens=300)
    message = raw.strip()
    if not message:
        raise LLMCallError("Model returned an empty citizen response")
    return message[:1000]
