from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.analytics import dashboard_service as svc
from app.api.deps import require_admin, require_officer
from app.core.enums import ModuleCode
from app.database.session import get_db
from app.models.user import User
from app.schemas.analytics import (
    AIClassificationStats,
    AIRoutingStats,
    CountByLabel,
    DepartmentPerformance,
    HotspotPoint,
    ModuleStatusCell,
    OverviewStats,
    PredictedHotspotsResponse,
    PredictedVolumeResponse,
    ResolutionTimeStats,
    TimeSeriesPoint,
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Dashboard"])

# All analytics endpoints are admin-only: this is the Admin Dashboard's data
# source. Officers get their own department-scoped stats in a later part;
# citizens have no need for aggregate views.


@router.get("/overview", response_model=OverviewStats)
def overview(module: ModuleCode | None = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return svc.get_overview(db, module)


@router.get("/status-distribution", response_model=list[CountByLabel])
def status_distribution(
    module: ModuleCode | None = None, date_from: date | None = None, date_to: date | None = None,
    db: Session = Depends(get_db), _admin=Depends(require_admin),
):
    return svc.get_status_distribution(db, module, date_from, date_to)


@router.get("/by-module", response_model=list[CountByLabel])
def by_module(
    date_from: date | None = None, date_to: date | None = None,
    db: Session = Depends(get_db), _admin=Depends(require_admin),
):
    return svc.get_by_module(db, date_from, date_to)


@router.get("/over-time", response_model=list[TimeSeriesPoint])
def over_time(
    granularity: str = Query(default="day", pattern="^(day|week|month|year)$"),
    module: ModuleCode | None = None, date_from: date | None = None, date_to: date | None = None,
    db: Session = Depends(get_db), _admin=Depends(require_admin),
):
    return svc.get_over_time(db, granularity, module, date_from, date_to)


@router.get("/module-status-matrix", response_model=list[ModuleStatusCell])
def module_status_matrix(
    date_from: date | None = None, date_to: date | None = None,
    db: Session = Depends(get_db), _admin=Depends(require_admin),
):
    return svc.get_module_status_matrix(db, date_from, date_to)


@router.get("/priority-distribution", response_model=list[CountByLabel])
def priority_distribution(
    module: ModuleCode | None = None, date_from: date | None = None, date_to: date | None = None,
    db: Session = Depends(get_db), _admin=Depends(require_admin),
):
    return svc.get_priority_distribution(db, module, date_from, date_to)


@router.get("/department-performance", response_model=list[DepartmentPerformance])
def department_performance(module: ModuleCode | None = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return svc.get_department_performance(db, module)


@router.get("/resolution-time", response_model=ResolutionTimeStats)
def resolution_time(module: ModuleCode | None = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return svc.get_avg_resolution_time(db, module)


@router.get("/category-distribution", response_model=list[CountByLabel])
def category_distribution(module: ModuleCode | None = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return svc.get_category_distribution(db, module)


@router.get("/language-distribution", response_model=list[CountByLabel])
def language_distribution(module: ModuleCode | None = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return svc.get_language_distribution(db, module)


@router.get("/ai-classification-stats", response_model=AIClassificationStats)
def ai_classification_stats(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return svc.get_ai_classification_stats(db)


@router.get("/ai-routing-stats", response_model=AIRoutingStats)
def ai_routing_stats(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    return svc.get_ai_routing_stats(db)


@router.get("/hotspots", response_model=list[HotspotPoint])
def hotspots(
    module: ModuleCode | None = None,
    precision: int = Query(default=2, ge=1, le=4, description="Decimal places for grid bucket size (2 ≈ 1.1km cells)"),
    db: Session = Depends(get_db), _admin=Depends(require_admin),
):
    return svc.get_hotspots(db, module, precision)


@router.get("/predicted-volume", response_model=PredictedVolumeResponse)
def predicted_volume(
    module: ModuleCode | None = None,
    days_ahead: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db), _admin=Depends(require_admin),
):
    result = svc.predict_volume(db, module, days_ahead)
    db.commit()
    return result


@router.get("/predicted-hotspots", response_model=PredictedHotspotsResponse)
def predicted_hotspots(module: ModuleCode | None = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    result = svc.predict_hotspots(db, module)
    db.commit()
    return result


@router.get("/my-department", response_model=OverviewStats)
def my_department_overview(db: Session = Depends(get_db), officer: User = Depends(require_officer)):
    """Department-scoped overview for the officer portal (admins hitting this need no department)."""
    if officer.department_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your account is not assigned to a department")
    return svc.get_department_overview(db, officer.department_id)


@router.post("/train-prediction-model")
def train_prediction_model(module: ModuleCode | None = None, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """
    Manually (re)trains the volume-forecast model — spec §11's "training
    pipeline" requirement. Requires PREDICTION_PROVIDER=sklearn or =xgboost
    and requirements-ai.txt installed; returns a clear error otherwise
    rather than silently doing nothing.
    """
    from app.analytics import ml_predictor

    try:
        metrics = ml_predictor.train_volume_model(db, module)
        db.commit()
        return {"success": True, "metrics": metrics}
    except ImportError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Training requires scikit-learn (and xgboost if PREDICTION_PROVIDER=xgboost) installed: {exc}",
        )
    except ml_predictor.InsufficientDataError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Not enough complaint history to train a model: {exc}")
