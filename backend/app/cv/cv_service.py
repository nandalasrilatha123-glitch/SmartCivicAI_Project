"""
Wires yolo_detector.analyze_image() to the CVAnalysis table. Called
synchronously right after an image is saved to disk (complaint submission
and the add-image endpoint) — CV_PROVIDER=demo (the default) returns
instantly with no model load, so this adds no meaningful latency out of
the box. When CV_PROVIDER=yolo, the first call in a process will pay the
one-time model-load cost; subsequent calls in the same process reuse
ultralytics' internal caching.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.cv.yolo_detector import analyze_image
from app.models.ai import CVAnalysis
from app.models.complaint import ComplaintImage

logger = logging.getLogger("smartcivicai.cv")


def analyze_and_store(db: Session, image: ComplaintImage) -> CVAnalysis:
    result = analyze_image(image.file_path)

    cv_analysis = CVAnalysis(
        image_id=image.id,
        provider=result["provider"],
        detected_objects=result["detected_objects"],
        confidence=result["confidence"],
        status=result["status"],
    )
    db.add(cv_analysis)
    db.flush()
    logger.info("CV analysis for image %s: provider=%s status=%s note=%s", image.id, result["provider"], result["status"], result.get("note"))
    return cv_analysis
