"""
Deterministic, dependency-light "demo mode" AI classifier.

This is what runs when AI_PROVIDER=demo (the default, and the only mode
guaranteed to work with zero API keys/models — spec §8 and §27). It is
intentionally rule-based rather than a stub: real keyword matching against
each category's `keywords` column, real severity heuristics for priority,
real language detection via `langdetect`.

When AI_PROVIDER=anthropic/openai (built in a later part), the same
CLASSIFICATION / PRIORITY / ROUTING output *shape* is produced by an LLM
call instead — callers (app/ai/pipeline.py) don't need to know which one
ran.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.enums import LanguageCode, PriorityLevel
from app.models.module import Category

# --- Priority keyword tiers (checked against original + translated text) ---
_CRITICAL_KEYWORDS = [
    "fire", "collapse", "collapsed", "died", "death", "dead", "drowning", "electrocution",
    "gas leak", "explosion", "life threatening", "life-threatening", "accident", "bleeding",
    "unconscious", "outbreak", "contaminated water", "building collapse",
]
_HIGH_KEYWORDS = [
    "urgent", "danger", "dangerous", "emergency", "severe", "critical", "no water", "no electricity",
    "sewage", "leaking", "exposed wire", "open manhole", "broken signal", "no doctor", "medicine shortage",
    "crop failure", "pest infestation", "flooding",
]
_LOW_KEYWORDS = [
    "minor", "small issue", "cosmetic", "suggestion", "request", "would be nice", "eventually",
]

# --- Simple keyword -> module signal used only when a complaint arrives without
# an explicit module selection from the citizen (defensive fallback; the UI
# normally always sends module explicitly since it's a required field). ---
_MODULE_KEYWORDS: dict[str, list[str]] = {
    "GOVERNMENT_SCHOOLS": ["school", "classroom", "teacher", "student", "mid-day meal", "midday meal"],
    "AGRICULTURE": ["crop", "farm", "irrigation", "fertilizer", "seed", "pest", "subsidy", "farmer"],
    "HEALTHCARE": ["hospital", "doctor", "nurse", "medicine", "ambulance", "clinic", "patient"],
    "TRAFFIC": ["traffic", "signal", "road", "parking", "accident", "pothole", "streetlight"],
}


@dataclass
class ClassificationResult:
    predicted_module: str
    predicted_category_id: str | None
    module_confidence: float
    category_confidence: float


@dataclass
class PriorityResult:
    priority: PriorityLevel
    confidence: float
    reasoning: str


def detect_language(text: str, declared_language: LanguageCode) -> tuple[str, float]:
    """
    Best-effort language detection using `langdetect`. Falls back to the
    citizen-declared language if detection fails or the package is missing
    (langdetect is a lightweight pure-Python dep listed in the core
    requirements.txt, not requirements-ai.txt, so this should normally work).
    """
    try:
        from langdetect import DetectorFactory, detect

        DetectorFactory.seed = 0  # deterministic results
        detected = detect(text)
        # langdetect uses ISO codes close enough to ours for en/hi; Telugu -> 'te'
        if detected in ("en", "hi", "te"):
            return detected, 0.85
        return declared_language.value, 0.5
    except Exception:
        return declared_language.value, 0.3


def classify_category(text: str, module_code: str, categories: list[Category]) -> ClassificationResult:
    """
    Matches complaint text against each active category's comma-separated
    `keywords` (falling back to matching the category's English name if no
    keywords are configured). Highest keyword-hit-count wins; confidence is
    scaled by how many distinct keywords matched.
    """
    text_lower = text.lower()
    best_category: Category | None = None
    best_score = 0
    best_matches = 0

    scoped_categories = [c for c in categories if c.is_active]

    for category in scoped_categories:
        terms = []
        if category.keywords:
            terms.extend([t.strip().lower() for t in category.keywords.split(",") if t.strip()])
        terms.append(category.name_en.lower())

        matches = sum(1 for term in terms if term and term in text_lower)
        if matches > best_score:
            best_score = matches
            best_matches = matches
            best_category = category

    if best_category is None:
        # Fall back to an "Other" category if present, else no category
        fallback = next((c for c in scoped_categories if c.name_en.strip().lower() == "other"), None)
        return ClassificationResult(
            predicted_module=module_code,
            predicted_category_id=str(fallback.id) if fallback else None,
            module_confidence=0.9,  # module is citizen-declared, so high confidence by construction
            category_confidence=0.3 if fallback else 0.15,
        )

    category_confidence = min(0.55 + (best_matches * 0.12), 0.97)
    return ClassificationResult(
        predicted_module=module_code,
        predicted_category_id=str(best_category.id),
        module_confidence=0.9,
        category_confidence=round(category_confidence, 2),
    )


def assess_priority(text: str) -> PriorityResult:
    text_lower = text.lower()

    critical_hits = [kw for kw in _CRITICAL_KEYWORDS if kw in text_lower]
    if critical_hits:
        return PriorityResult(
            priority=PriorityLevel.CRITICAL,
            confidence=min(0.6 + 0.1 * len(critical_hits), 0.95),
            reasoning=f"Critical-severity keywords detected: {', '.join(critical_hits[:3])}",
        )

    high_hits = [kw for kw in _HIGH_KEYWORDS if kw in text_lower]
    if high_hits:
        return PriorityResult(
            priority=PriorityLevel.HIGH,
            confidence=min(0.55 + 0.08 * len(high_hits), 0.9),
            reasoning=f"High-severity keywords detected: {', '.join(high_hits[:3])}",
        )

    low_hits = [kw for kw in _LOW_KEYWORDS if kw in text_lower]
    if low_hits:
        return PriorityResult(
            priority=PriorityLevel.LOW,
            confidence=0.6,
            reasoning=f"Low-severity language detected: {', '.join(low_hits[:2])}",
        )

    # Length/urgency-punctuation heuristic as a last resort
    exclamations = text.count("!")
    if exclamations >= 2:
        return PriorityResult(
            priority=PriorityLevel.HIGH,
            confidence=0.45,
            reasoning="Multiple exclamation marks suggest urgency, but no explicit severity keywords found.",
        )

    return PriorityResult(
        priority=PriorityLevel.MEDIUM,
        confidence=0.5,
        reasoning="No strong severity signals found; defaulted to MEDIUM priority for manual triage.",
    )


_ACK_TEMPLATES: dict[str, dict[str, str]] = {
    "en": {
        "template": "Thank you for reporting this {module} issue. Your complaint (priority: {priority}) has been "
                     "registered and routed to the {department} for action. You can track progress anytime.",
    },
    "te": {
        "template": "ఈ {module} సమస్యను నివేదించినందుకు ధన్యవాదాలు. మీ ఫిర్యాదు (ప్రాధాన్యత: {priority}) నమోదు చేయబడింది మరియు "
                     "చర్య కోసం {department}కు పంపబడింది. మీరు ఎప్పుడైనా పురోగతిని ట్రాక్ చేయవచ్చు.",
    },
    "hi": {
        "template": "इस {module} समस्या की रिपोर्ट करने के लिए धन्यवाद। आपकी शिकायत (प्राथमिकता: {priority}) दर्ज कर ली गई है "
                     "और कार्रवाई हेतु {department} को भेज दी गई है। आप कभी भी प्रगति ट्रैक कर सकते हैं।",
    },
}


def generate_citizen_response(module_label: str, priority: PriorityLevel, department_name: str, language: str) -> str:
    tpl = _ACK_TEMPLATES.get(language, _ACK_TEMPLATES["en"])["template"]
    return tpl.format(module=module_label, priority=priority.value, department=department_name)
