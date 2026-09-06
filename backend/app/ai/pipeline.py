"""
Orchestrates the language-detection -> classification -> priority ->
routing -> citizen-response workflow described in spec §9 and persists
results as AIAnalysis + AIClassification + AIPriority + AIRouting.

Provider selection (AI_PROVIDER in .env):
  demo        -> app.ai.demo_classifier — rule-based, zero dependencies,
                 always available, used when nothing else is configured.
  anthropic   -> app.ai.langgraph_pipeline (LangGraph + Claude via the
                 anthropic SDK). Attempted only when ANTHROPIC_API_KEY is
                 also set. On ANY failure — package not installed, bad key,
                 rate limit, timeout, malformed model output — this module
                 catches it and falls back to demo_classifier for that
                 complaint. The failure reason is recorded in
                 ai_analysis.raw_error so it's visible on the admin AI
                 Monitoring dashboard rather than silently swallowed.

Nothing in this module imports langgraph/anthropic at module load time —
the import happens inside the try block below, only when AI_PROVIDER=
anthropic is actually configured, so installations without
requirements-ai.txt are completely unaffected (spec §23/§27).
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.ai import demo_classifier
from app.core.config import settings
from app.core.enums import ComplaintStatus
from app.models.ai import AIAnalysis, AIClassification, AIPriority, AIRouting
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.module import Category, Module

logger = logging.getLogger("smartcivicai.ai")

_MODULE_LABELS = {
    "GOVERNMENT_SCHOOLS": "Government Schools",
    "AGRICULTURE": "Agriculture",
    "HEALTHCARE": "Healthcare",
    "TRAFFIC": "Traffic",
}


def _try_llm_pipeline(complaint: Complaint, categories: list[Category], department: Department | None) -> tuple[dict | None, str | None]:
    """Returns (result_dict, None) on success, or (None, error_message) on any failure."""
    if settings.AI_PROVIDER == "demo":
        return None, None
    if settings.AI_PROVIDER not in ("anthropic",):
        return None, f"AI_PROVIDER='{settings.AI_PROVIDER}' is not implemented in this build (only 'anthropic' is); used demo classification instead."
    if not settings.ANTHROPIC_API_KEY:
        return None, "AI_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set; used demo classification instead."

    try:
        from app.ai.langgraph_pipeline import run_langgraph_pipeline

        result = run_langgraph_pipeline(
            complaint_text=complaint.original_text,
            language=complaint.original_language.value,
            module_code=complaint.module.value,
            module_label=_MODULE_LABELS.get(complaint.module.value, complaint.module.value),
            categories=[{"id": str(c.id), "name_en": c.name_en} for c in categories if c.is_active],
            department_id=str(department.id) if department else None,
            department_name=department.name if department else None,
        )
        return result, None
    except ImportError as exc:
        return None, f"langgraph/anthropic not installed ({exc}); used demo classification instead."
    except Exception as exc:  # noqa: BLE001 — any LLM failure must fall back, never crash submission
        logger.warning("LangGraph/Anthropic pipeline failed, falling back to demo: %s", exc)
        return None, f"LLM pipeline failed ({exc}); used demo classification instead."


def run_ai_pipeline(db: Session, complaint: Complaint) -> AIAnalysis:
    workflow_trace: list[dict] = []

    # --- Stage 0: language detection (always demo/langdetect — this is a
    # cheap deterministic step outside the 4-agent LangGraph workflow in
    # spec §9's diagram, so it runs the same way regardless of provider) ---
    detected_language, lang_confidence = demo_classifier.detect_language(
        complaint.original_text, complaint.original_language
    )
    workflow_trace.append({"stage": "language_detection", "result": detected_language, "confidence": lang_confidence})

    module_row = db.query(Module).filter(Module.code == complaint.module).first()
    categories: list[Category] = module_row.categories if module_row else []

    department = (
        db.query(Department)
        .filter(Department.module == complaint.module)
        .order_by(Department.created_at)
        .first()
    )

    # --- Stages 1-4: try the real LLM pipeline, fall back to demo ---
    llm_result, fallback_reason = _try_llm_pipeline(complaint, categories, department)

    if llm_result is not None:
        provider = "anthropic"
        predicted_category_id = llm_result["predicted_category_id"]
        category_confidence = llm_result["category_confidence"]
        module_confidence = llm_result["module_confidence"]
        priority = llm_result["priority"]
        priority_confidence = llm_result["priority_confidence"]
        priority_reasoning = llm_result["priority_reasoning"]
        routing_confidence = llm_result["routing_confidence"]
        citizen_response = llm_result["citizen_response"]
        raw_error = None
    else:
        provider = "demo"
        raw_error = fallback_reason
        if fallback_reason:
            logger.info(fallback_reason)

        classification = demo_classifier.classify_category(complaint.original_text, complaint.module.value, categories)
        priority_result = demo_classifier.assess_priority(complaint.original_text)

        predicted_category_id = classification.predicted_category_id
        category_confidence = classification.category_confidence
        module_confidence = classification.module_confidence
        priority = priority_result.priority
        priority_confidence = priority_result.confidence
        priority_reasoning = priority_result.reasoning
        routing_confidence = 0.8 if department else 0.0
        citizen_response = demo_classifier.generate_citizen_response(
            _MODULE_LABELS.get(complaint.module.value, complaint.module.value),
            priority, department.name if department else "the relevant department (pending manual assignment)",
            complaint.original_language.value,
        )

    workflow_trace.append({
        "stage": "classification", "provider": provider,
        "predicted_category_id": predicted_category_id, "module_confidence": module_confidence, "category_confidence": category_confidence,
    })
    workflow_trace.append({
        "stage": "priority_assessment", "provider": provider,
        "priority": priority.value, "confidence": priority_confidence, "reasoning": priority_reasoning,
    })
    workflow_trace.append({
        "stage": "routing", "provider": "demo (deterministic lookup regardless of AI_PROVIDER)",
        "predicted_department_id": str(department.id) if department else None, "confidence": routing_confidence,
    })
    workflow_trace.append({"stage": "citizen_response", "provider": provider, "generated": True})

    overall_confidence = round((module_confidence + category_confidence + priority_confidence + routing_confidence) / 4, 2)
    requires_review = overall_confidence < settings.AI_CONFIDENCE_THRESHOLD or department is None

    # --- Persist ---
    analysis = AIAnalysis(
        complaint_id=complaint.id,
        provider=provider,
        detected_language=detected_language,
        entities=None,
        intent=f"report_{complaint.module.value.lower()}_issue",
        citizen_response_text=citizen_response,
        overall_confidence=overall_confidence,
        requires_admin_review=requires_review,
        workflow_trace={"steps": workflow_trace},
        raw_error=raw_error,
    )
    db.add(analysis)
    db.flush()

    db.add(AIClassification(
        analysis_id=analysis.id,
        predicted_module=complaint.module,
        predicted_category_id=uuid.UUID(predicted_category_id) if predicted_category_id else None,
        module_confidence=module_confidence,
        category_confidence=category_confidence,
    ))
    db.add(AIPriority(
        analysis_id=analysis.id,
        predicted_priority=priority,
        confidence=priority_confidence,
        reasoning=priority_reasoning,
    ))
    db.add(AIRouting(
        analysis_id=analysis.id,
        predicted_department_id=department.id if department else None,
        confidence=routing_confidence,
    ))

    # --- Apply AI results onto the complaint itself (citizen can still not
    # have picked a category; admin/officer can always override later) ---
    if complaint.category_id is None and predicted_category_id:
        complaint.category_id = uuid.UUID(predicted_category_id)
    complaint.priority = priority
    if department:
        complaint.department_id = department.id
    complaint.summary = complaint.original_text[:200] + ("..." if len(complaint.original_text) > 200 else "")
    complaint.status = ComplaintStatus.REQUIRES_ADMIN_REVIEW if requires_review else ComplaintStatus.PENDING

    db.flush()
    return analysis
