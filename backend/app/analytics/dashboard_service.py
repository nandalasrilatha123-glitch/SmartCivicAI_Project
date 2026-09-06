"""
All aggregation logic backing the admin dashboard's charts (spec §6).
Every function queries live data — nothing here is hard-coded, per spec §29.

Predictive charts (14/15): predict_volume and predict_hotspots try a real
model first — XGBoost/scikit-learn (app/analytics/ml_predictor.py) and
DBSCAN clustering respectively — when PREDICTION_PROVIDER is 'xgboost' or
'sklearn'. On ImportError (package not installed) or InsufficientDataError
(not enough history to fit anything meaningful), they fall back to the
dependency-free linear-trend / grid-bucket heuristics below, exactly like
the LangGraph AI pipeline falls back to the demo classifier in Part 8.
Every response — heuristic or trained model — sets is_demo_data honestly
rather than presenting extrapolated numbers as ground truth.
"""
from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import ComplaintStatus, ModuleCode, PriorityLevel
from app.models.ai import AIAnalysis, AIClassification, AIRouting
from app.models.complaint import Complaint, ComplaintStatusHistory
from app.models.department import Department
from app.models.misc import PredictionResult
from app.models.module import Category

logger = logging.getLogger("smartcivicai.analytics")

_OPEN_STATUSES = (
    ComplaintStatus.NEW, ComplaintStatus.PENDING, ComplaintStatus.ASSIGNED,
    ComplaintStatus.IN_PROGRESS, ComplaintStatus.ESCALATED, ComplaintStatus.REQUIRES_ADMIN_REVIEW,
)


def _apply_common_filters(query, module: ModuleCode | None, date_from: date | None, date_to: date | None):
    if module:
        query = query.filter(Complaint.module == module)
    if date_from:
        query = query.filter(Complaint.created_at >= date_from)
    if date_to:
        query = query.filter(Complaint.created_at <= date_to)
    return query


def get_overview(db: Session, module: ModuleCode | None = None) -> dict:
    query = db.query(Complaint)
    if module:
        query = query.filter(Complaint.module == module)

    now = datetime.now(timezone.utc)
    overdue_cutoff = now - timedelta(days=7)

    counts_by_status = dict(
        query.with_entities(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status).all()
    )

    total = sum(counts_by_status.values())
    overdue = query.filter(
        Complaint.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED]),
        Complaint.created_at < overdue_cutoff,
    ).count()
    high_priority = query.filter(
        Complaint.priority.in_([PriorityLevel.HIGH, PriorityLevel.CRITICAL]),
        Complaint.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED]),
    ).count()

    return {
        "total": total,
        "new": counts_by_status.get(ComplaintStatus.NEW, 0),
        "pending": counts_by_status.get(ComplaintStatus.PENDING, 0),
        "assigned": counts_by_status.get(ComplaintStatus.ASSIGNED, 0),
        "in_progress": counts_by_status.get(ComplaintStatus.IN_PROGRESS, 0),
        "resolved": counts_by_status.get(ComplaintStatus.RESOLVED, 0),
        "rejected": counts_by_status.get(ComplaintStatus.REJECTED, 0),
        "escalated": counts_by_status.get(ComplaintStatus.ESCALATED, 0),
        "requires_admin_review": counts_by_status.get(ComplaintStatus.REQUIRES_ADMIN_REVIEW, 0),
        "overdue": overdue,
        "high_priority": high_priority,
    }


def get_department_overview(db: Session, department_id) -> dict:
    """Same shape as get_overview but scoped to one department — powers the officer portal."""
    query = db.query(Complaint).filter(Complaint.department_id == department_id)

    now = datetime.now(timezone.utc)
    overdue_cutoff = now - timedelta(days=7)

    counts_by_status = dict(
        query.with_entities(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status).all()
    )
    total = sum(counts_by_status.values())
    overdue = query.filter(
        Complaint.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED]),
        Complaint.created_at < overdue_cutoff,
    ).count()
    high_priority = query.filter(
        Complaint.priority.in_([PriorityLevel.HIGH, PriorityLevel.CRITICAL]),
        Complaint.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED]),
    ).count()

    return {
        "total": total,
        "new": counts_by_status.get(ComplaintStatus.NEW, 0),
        "pending": counts_by_status.get(ComplaintStatus.PENDING, 0),
        "assigned": counts_by_status.get(ComplaintStatus.ASSIGNED, 0),
        "in_progress": counts_by_status.get(ComplaintStatus.IN_PROGRESS, 0),
        "resolved": counts_by_status.get(ComplaintStatus.RESOLVED, 0),
        "rejected": counts_by_status.get(ComplaintStatus.REJECTED, 0),
        "escalated": counts_by_status.get(ComplaintStatus.ESCALATED, 0),
        "requires_admin_review": counts_by_status.get(ComplaintStatus.REQUIRES_ADMIN_REVIEW, 0),
        "overdue": overdue,
        "high_priority": high_priority,
    }


def get_status_distribution(db: Session, module: ModuleCode | None, date_from: date | None, date_to: date | None) -> list[dict]:
    query = db.query(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status)
    query = _apply_common_filters(query, module, date_from, date_to)
    return [{"label": status.value, "count": count} for status, count in query.all()]


def get_by_module(db: Session, date_from: date | None, date_to: date | None) -> list[dict]:
    query = db.query(Complaint.module, func.count(Complaint.id)).group_by(Complaint.module)
    query = _apply_common_filters(query, None, date_from, date_to)
    return [{"label": module.value, "count": count} for module, count in query.all()]


def get_over_time(
    db: Session, granularity: str, module: ModuleCode | None, date_from: date | None, date_to: date | None
) -> list[dict]:
    granularity = granularity if granularity in ("day", "week", "month", "year") else "day"
    trunc = func.date_trunc(granularity, Complaint.created_at)
    query = db.query(trunc.label("period"), func.count(Complaint.id)).group_by(trunc).order_by(trunc)
    query = _apply_common_filters(query, module, date_from, date_to)
    return [{"period": period.date().isoformat(), "count": count} for period, count in query.all()]


def get_module_status_matrix(db: Session, date_from: date | None, date_to: date | None) -> list[dict]:
    query = db.query(Complaint.module, Complaint.status, func.count(Complaint.id)).group_by(Complaint.module, Complaint.status)
    query = _apply_common_filters(query, None, date_from, date_to)
    return [{"module": m.value, "status": s.value, "count": c} for m, s, c in query.all()]


def get_priority_distribution(db: Session, module: ModuleCode | None, date_from: date | None, date_to: date | None) -> list[dict]:
    query = db.query(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority)
    query = _apply_common_filters(query, module, date_from, date_to)
    return [{"label": priority.value, "count": count} for priority, count in query.all()]


def get_department_performance(db: Session, module: ModuleCode | None = None) -> list[dict]:
    dept_query = db.query(Department)
    if module:
        dept_query = dept_query.filter(Department.module == module)
    departments = dept_query.all()

    results = []
    for dept in departments:
        received = db.query(func.count(Complaint.id)).filter(Complaint.department_id == dept.id).scalar() or 0
        resolved = (
            db.query(func.count(Complaint.id))
            .filter(Complaint.department_id == dept.id, Complaint.status == ComplaintStatus.RESOLVED)
            .scalar() or 0
        )
        pending = (
            db.query(func.count(Complaint.id))
            .filter(Complaint.department_id == dept.id, Complaint.status.in_(_OPEN_STATUSES))
            .scalar() or 0
        )
        resolution_rate = round((resolved / received) * 100, 1) if received else 0.0
        results.append({
            "department_id": str(dept.id),
            "department_name": dept.name,
            "module": dept.module.value,
            "received": received,
            "resolved": resolved,
            "pending": pending,
            "resolution_rate": resolution_rate,
        })
    return results


def get_avg_resolution_time(db: Session, module: ModuleCode | None = None) -> dict:
    """
    Uses the first RESOLVED entry in complaint_status_history (more accurate
    than complaint.updated_at, which can shift for other reasons after
    resolution, e.g. a late admin override).
    """
    query = (
        db.query(Complaint.id, Complaint.module, Complaint.created_at, func.min(ComplaintStatusHistory.created_at))
        .join(ComplaintStatusHistory, ComplaintStatusHistory.complaint_id == Complaint.id)
        .filter(ComplaintStatusHistory.to_status == ComplaintStatus.RESOLVED)
        .group_by(Complaint.id, Complaint.module, Complaint.created_at)
    )
    if module:
        query = query.filter(Complaint.module == module)

    durations_hours: list[float] = []
    by_module_durations: dict[str, list[float]] = defaultdict(list)

    for _id, mod, created_at, resolved_at in query.all():
        hours = (resolved_at - created_at).total_seconds() / 3600
        if hours < 0:
            continue
        durations_hours.append(hours)
        by_module_durations[mod.value].append(hours)

    overall_avg = round(statistics.mean(durations_hours), 1) if durations_hours else None
    by_module = [
        {"module": mod, "avg_hours": round(statistics.mean(hrs), 1), "resolved_count": len(hrs)}
        for mod, hrs in by_module_durations.items()
    ]
    return {"overall_avg_hours": overall_avg, "by_module": by_module}


def get_category_distribution(db: Session, module: ModuleCode | None = None) -> list[dict]:
    query = (
        db.query(Category.name_en, func.count(Complaint.id))
        .join(Complaint, Complaint.category_id == Category.id)
        .group_by(Category.name_en)
    )
    if module:
        query = query.filter(Complaint.module == module)
    return [{"label": name, "count": count} for name, count in query.all()]


def get_language_distribution(db: Session, module: ModuleCode | None = None) -> list[dict]:
    query = db.query(Complaint.original_language, func.count(Complaint.id)).group_by(Complaint.original_language)
    if module:
        query = query.filter(Complaint.module == module)
    return [{"label": lang.value, "count": count} for lang, count in query.all()]


def get_ai_classification_stats(db: Session) -> dict:
    total = db.query(func.count(AIAnalysis.id)).scalar() or 0
    requires_review = db.query(func.count(AIAnalysis.id)).filter(AIAnalysis.requires_admin_review.is_(True)).scalar() or 0

    avg_module_conf = db.query(func.avg(AIClassification.module_confidence)).scalar()
    avg_category_conf = db.query(func.avg(AIClassification.category_confidence)).scalar()
    overridden = db.query(func.count(AIClassification.id)).filter(AIClassification.is_overridden.is_(True)).scalar() or 0

    return {
        "total_analyzed": total,
        "avg_module_confidence": round(float(avg_module_conf), 2) if avg_module_conf is not None else None,
        "avg_category_confidence": round(float(avg_category_conf), 2) if avg_category_conf is not None else None,
        "overridden_count": overridden,
        "override_rate": round((overridden / total) * 100, 1) if total else 0.0,
        "requires_review_count": requires_review,
    }


def get_ai_routing_stats(db: Session) -> dict:
    total = db.query(func.count(AIRouting.id)).scalar() or 0
    avg_conf = db.query(func.avg(AIRouting.confidence)).scalar()
    overridden = db.query(func.count(AIRouting.id)).filter(AIRouting.is_overridden.is_(True)).scalar() or 0
    unrouted = db.query(func.count(AIRouting.id)).filter(AIRouting.predicted_department_id.is_(None)).scalar() or 0

    return {
        "total_routed": total,
        "avg_confidence": round(float(avg_conf), 2) if avg_conf is not None else None,
        "overridden_count": overridden,
        "unrouted_count": unrouted,
    }


def get_hotspots(db: Session, module: ModuleCode | None = None, precision: int = 2) -> list[dict]:
    """
    Buckets complaints into a lat/lng grid (rounded to `precision` decimal
    places — 2 decimals is roughly a 1.1km x 1.1km cell) and returns each
    bucket's count plus its dominant module and priority, for the GIS
    hotspot overlay.
    """
    query = db.query(Complaint.latitude, Complaint.longitude, Complaint.module, Complaint.priority).filter(
        Complaint.latitude.isnot(None), Complaint.longitude.isnot(None)
    )
    if module:
        query = query.filter(Complaint.module == module)

    buckets: dict[tuple[float, float], list[tuple[str, str]]] = defaultdict(list)
    for lat, lng, mod, pri in query.all():
        key = (round(lat, precision), round(lng, precision))
        buckets[key].append((mod.value, pri.value))

    results = []
    for (lat, lng), entries in buckets.items():
        modules_seen = [m for m, _ in entries]
        priorities_seen = [p for _, p in entries]
        results.append({
            "latitude": lat,
            "longitude": lng,
            "count": len(entries),
            "dominant_module": max(set(modules_seen), key=modules_seen.count),
            "dominant_priority": max(set(priorities_seen), key=priorities_seen.count),
        })
    return sorted(results, key=lambda r: r["count"], reverse=True)


def _predict_volume_heuristic(db: Session, module: ModuleCode | None, days_ahead: int) -> dict:
    """Dependency-free linear-trend fallback — see predict_volume()."""
    today = date.today()
    window_start = today - timedelta(days=29)

    query = db.query(func.date(Complaint.created_at), func.count(Complaint.id)).filter(
        func.date(Complaint.created_at) >= window_start
    ).group_by(func.date(Complaint.created_at))
    if module:
        query = query.filter(Complaint.module == module)

    counts_by_day = {d: c for d, c in query.all()}
    series = [counts_by_day.get(window_start + timedelta(days=i), 0) for i in range(30)]

    x = list(range(30))
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(series)
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, series))
    denominator = sum((xi - x_mean) ** 2 for xi in x) or 1
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    points = []
    for i in range(1, days_ahead + 1):
        predicted = max(0.0, round(intercept + slope * (30 + i - 1), 1))
        target_date = today + timedelta(days=i)
        points.append({"date": target_date.isoformat(), "predicted_count": predicted, "module": module.value if module else None})

    return {
        "is_demo_data": True,
        "model_name": "demo_linear_trend",
        "points": points,
        "note": (
            "Heuristic linear-trend projection over the last 30 days of complaint volume "
            "(dependency-free fallback — see raw_note for why the trained-model path wasn't used)."
        ),
    }


def predict_volume(db: Session, module: ModuleCode | None, days_ahead: int, persist: bool = True) -> dict:
    """
    Tries a real trained model (XGBoost or scikit-learn, per
    PREDICTION_PROVIDER) first; falls back to a dependency-free linear-trend
    heuristic on ImportError (package not installed) or InsufficientDataError
    (not enough history to fit anything meaningful). See module docstring.
    """
    result = None
    if settings.PREDICTION_PROVIDER in ("xgboost", "sklearn"):
        try:
            from app.analytics import ml_predictor

            result = ml_predictor.predict_volume_ml(db, module, days_ahead)
        except ImportError as exc:
            logger.info("Prediction packages not installed (%s), falling back to heuristic", exc)
        except ml_predictor.InsufficientDataError as exc:
            logger.info("Not enough history to train a volume model (%s), falling back to heuristic", exc)
        except Exception as exc:  # noqa: BLE001 — any training/prediction failure must fall back, never 500
            logger.warning("ML volume prediction failed (%s), falling back to heuristic", exc)

    if result is None:
        result = _predict_volume_heuristic(db, module, days_ahead)

    if persist:
        db.add(PredictionResult(
            prediction_type="volume_forecast",
            module=module,
            target_date=date.today().isoformat(),
            payload={"points": result["points"]},
            model_name=result["model_name"],
            model_metrics=None,
            is_demo_data=True,
        ))
        db.flush()

    return result


def _predict_hotspots_heuristic(db: Session, module: ModuleCode | None) -> dict:
    """Dependency-free grid-bucket frequency ranking — see predict_hotspots()."""
    window_start = datetime.now(timezone.utc) - timedelta(days=30)
    query = db.query(Complaint.latitude, Complaint.longitude, Complaint.module).filter(
        Complaint.latitude.isnot(None), Complaint.longitude.isnot(None), Complaint.created_at >= window_start
    )
    if module:
        query = query.filter(Complaint.module == module)

    buckets: dict[tuple[float, float], list[str]] = defaultdict(list)
    for lat, lng, mod in query.all():
        buckets[(round(lat, 2), round(lng, 2))].append(mod.value)

    if not buckets:
        return {"is_demo_data": True, "model_name": "demo_frequency_heuristic", "areas": [], "note": "No recent complaint data available to project risk areas from."}

    max_count = max(len(v) for v in buckets.values())
    areas = []
    for (lat, lng), mods in sorted(buckets.items(), key=lambda kv: len(kv[1]), reverse=True)[:20]:
        areas.append({
            "latitude": lat,
            "longitude": lng,
            "risk_score": round(len(mods) / max_count, 2),
            "recent_count": len(mods),
            "module": max(set(mods), key=mods.count),
        })

    return {
        "is_demo_data": True,
        "model_name": "demo_frequency_heuristic",
        "areas": areas,
        "note": "Heuristic ranking by recent (30-day) complaint frequency per fixed grid cell (dependency-free fallback).",
    }


def predict_hotspots(db: Session, module: ModuleCode | None = None, persist: bool = True) -> dict:
    """
    Tries real DBSCAN spatial clustering (scikit-learn) first when
    PREDICTION_PROVIDER is 'sklearn'/'xgboost'; falls back to the fixed-grid
    frequency heuristic on ImportError or InsufficientDataError.
    """
    result = None
    if settings.PREDICTION_PROVIDER in ("xgboost", "sklearn"):
        try:
            from app.analytics import ml_predictor

            clusters = ml_predictor.cluster_hotspots_dbscan(db, module)
            areas = [
                {**c, "risk_score": round(c["count"] / max(cl["count"] for cl in clusters), 2)}
                for c in clusters
            ][:20]
            result = {
                "is_demo_data": True,
                "model_name": "dbscan_clustering",
                "areas": areas,
                "note": (
                    "DBSCAN spatial clustering (haversine distance, ~1km radius) over all geotagged complaints — "
                    "a real spatial ML method, but run on synthetic seed data, so treat cluster locations as "
                    "illustrative rather than validated real-world hotspots."
                ),
            }
        except ImportError as exc:
            logger.info("Clustering packages not installed (%s), falling back to grid heuristic", exc)
        except ml_predictor.InsufficientDataError as exc:
            logger.info("Not enough geotagged complaints to cluster (%s), falling back to grid heuristic", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DBSCAN hotspot clustering failed (%s), falling back to grid heuristic", exc)

    if result is None:
        result = _predict_hotspots_heuristic(db, module)

    if persist:
        db.add(PredictionResult(
            prediction_type="hotspot",
            module=module,
            target_date=date.today().isoformat(),
            payload={"areas": result["areas"]},
            model_name=result["model_name"],
            model_metrics=None,
            is_demo_data=True,
        ))
        db.flush()

    return result
