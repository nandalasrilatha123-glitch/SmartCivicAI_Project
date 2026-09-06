"""
Image analysis for complaint photos (spec §10). CV_PROVIDER in .env
controls behavior:

  demo (default) -> no object detection is attempted at all. Returns an
                     empty detection list with a clear note. This is the
                     honest choice per spec §10's explicit warning: "Do not
                     pretend a model can detect classes for which no
                     trained weights exist." We have no trained weights for
                     civic-issue classes (road damage, garbage, water
                     leakage, etc.) — nobody does, out of the box — so demo
                     mode does not fabricate detections.

  yolo            -> looks for a custom-trained model at YOLO_WEIGHTS_PATH
                     (default: models/yolo/civic_issues.pt — see
                     models/yolo/README.md for how to train and place one).
                     If found, runs REAL inference with REAL civic-issue
                     class labels and confidences.
                     If NOT found, falls back to a genuinely-run but
                     honestly-labeled generic object detector: ultralytics'
                     stock "yolov8n.pt" (COCO-pretrained, auto-downloaded by
                     the ultralytics package on first use — requires
                     network on whoever's machine runs this). Its detected
                     classes (person, car, traffic light, etc.) are
                     prefixed "coco:" and the result is still marked
                     ANALYZED_DEMO, not ANALYZED_MODEL — it is real object
                     detection, just not trained on civic-issue classes, so
                     it must never be presented as if it were.

Every failure mode (package not installed, weights corrupt, no network to
fetch the stock model, image unreadable) falls back to the no-detection
demo result rather than raising — image analysis must never break
complaint submission, per the same philosophy as the AI and prediction
pipelines in this project.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings
from app.core.enums import ImageAnalysisStatus

logger = logging.getLogger("smartcivicai.cv")

# Resolved relative to the backend/ directory (this file lives at
# backend/app/cv/yolo_detector.py, so parents[2] is backend/).
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _demo_result(note: str) -> dict:
    return {
        "provider": "demo",
        "detected_objects": [],
        "confidence": None,
        "status": ImageAnalysisStatus.ANALYZED_DEMO,
        "note": note,
    }


def analyze_image(image_path: str) -> dict:
    """
    image_path: path relative to UPLOAD_DIR (as stored in ComplaintImage.file_path).
    Returns a dict matching CVAnalysis columns: provider, detected_objects, confidence, status.
    """
    if settings.CV_PROVIDER != "yolo":
        return _demo_result("CV_PROVIDER=demo — no object detection attempted (see spec §10: no fabricated detections without trained weights).")

    full_image_path = Path(settings.UPLOAD_DIR) / image_path
    if not full_image_path.exists():
        return _demo_result(f"Image file not found on disk: {full_image_path}")

    custom_weights_path = _BACKEND_ROOT / settings.YOLO_WEIGHTS_PATH
    try:
        return _run_yolo(full_image_path, custom_weights_path)
    except ImportError as exc:
        logger.info("ultralytics/opencv not installed (%s), image analysis skipped", exc)
        return _demo_result(f"ultralytics/opencv-python not installed: {exc}. Install requirements-ai.txt to enable CV.")
    except Exception as exc:  # noqa: BLE001 — CV must never crash the request
        logger.warning("YOLO inference failed (%s), falling back to demo result", exc)
        return _demo_result(f"Image analysis failed: {exc}")


def _run_yolo(image_path: Path, custom_weights_path: Path) -> dict:
    from ultralytics import YOLO

    if custom_weights_path.exists():
        model = YOLO(str(custom_weights_path))
        label_prefix = ""
        status = ImageAnalysisStatus.ANALYZED_MODEL
        note = f"Custom-trained civic-issue model loaded from {custom_weights_path}."
    else:
        # Generic COCO-pretrained fallback — real detections, wrong domain.
        # ultralytics auto-downloads yolov8n.pt to its cache dir if missing.
        model = YOLO("yolov8n.pt")
        label_prefix = "coco:"
        status = ImageAnalysisStatus.ANALYZED_DEMO
        note = (
            f"No custom civic-issue model found at {custom_weights_path} — ran the generic COCO-pretrained "
            "yolov8n instead. These are real detections but NOT civic-issue-specific (e.g. 'coco:car', not "
            "'pothole'). Train and place a custom model at that path for real civic-class detection — "
            "see models/yolo/README.md."
        )

    results = model.predict(source=str(image_path), verbose=False)
    detections = []
    max_confidence = 0.0

    for result in results:
        names = result.names
        for box in result.boxes:
            label = f"{label_prefix}{names[int(box.cls[0])]}"
            confidence = float(box.conf[0])
            xyxy = [round(float(v), 1) for v in box.xyxy[0].tolist()]
            detections.append({"label": label, "confidence": round(confidence, 3), "bbox": xyxy})
            max_confidence = max(max_confidence, confidence)

    return {
        "provider": "yolo",
        "detected_objects": detections,
        "confidence": round(max_confidence, 3) if detections else None,
        "status": status,
        "note": note,
    }
