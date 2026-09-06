"""
Real (non-heuristic) predictive analytics, used when PREDICTION_PROVIDER is
'sklearn' or 'xgboost' (see .env.example / app/core/config.py). Every
function here has a hard dependency on pandas/numpy/scikit-learn (and
xgboost for the 'xgboost' provider) — all lazily imported so this module
can be imported even when requirements-ai.txt hasn't been installed.
dashboard_service.py catches ImportError/any training or prediction
failure and falls back to the dependency-free linear-trend/frequency
heuristics from Part 3, per the same fallback philosophy as the LangGraph
AI pipeline in Part 8.

IMPORTANT — spec §11 demo-data honesty requirement: this project's seed
data is ~60 synthetic complaints over ~4 months. That is nowhere near
enough real history to produce a trustworthy forecast, no matter how
sophisticated the model. Every result from this module still carries
is_demo_data=True and a metrics block, so nobody mistakes "a real
algorithm ran" for "this is a validated production forecast." The value
here is a genuine, inspectable training pipeline you can point at real
data later — not a claim that today's numbers are meaningful.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import ModuleCode
from app.models.complaint import Complaint

logger = logging.getLogger("smartcivicai.ml")

MODELS_DIR = Path(__file__).resolve().parents[3] / "models" / "trained"
MIN_TRAINING_DAYS = 14  # below this, a fitted model is more noise than signal


class InsufficientDataError(Exception):
    """Raised when there isn't enough history to fit a meaningful model."""


def _model_path(module: ModuleCode | None) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = module.value if module else "all"
    return MODELS_DIR / f"volume_{suffix}.joblib"


def _build_daily_series(db: Session, module: ModuleCode | None) -> "pd.DataFrame":  # noqa: F821
    import pandas as pd

    query = db.query(func.date(Complaint.created_at).label("day"), func.count(Complaint.id).label("count"))
    if module:
        query = query.filter(Complaint.module == module)
    query = query.group_by("day").order_by("day")

    rows = query.all()
    if not rows:
        raise InsufficientDataError("No complaint history at all for this module.")

    df = pd.DataFrame(rows, columns=["day", "count"])
    df["day"] = pd.to_datetime(df["day"])
    full_range = pd.date_range(df["day"].min(), df["day"].max(), freq="D")
    df = df.set_index("day").reindex(full_range, fill_value=0).rename_axis("day").reset_index()

    if len(df) < MIN_TRAINING_DAYS:
        raise InsufficientDataError(f"Only {len(df)} days of history — need at least {MIN_TRAINING_DAYS}.")

    return df


def _engineer_features(df: "pd.DataFrame"):  # noqa: F821
    import numpy as np

    df = df.copy()
    df["day_of_week"] = df["day"].dt.dayofweek
    df["day_of_month"] = df["day"].dt.day
    df["days_since_start"] = (df["day"] - df["day"].min()).dt.days
    df["rolling_7"] = df["count"].rolling(7, min_periods=1).mean().shift(1).fillna(0)
    df["rolling_3"] = df["count"].rolling(3, min_periods=1).mean().shift(1).fillna(0)

    feature_cols = ["day_of_week", "day_of_month", "days_since_start", "rolling_7", "rolling_3"]
    X = df[feature_cols].to_numpy()
    y = df["count"].to_numpy()
    return X, y, feature_cols, df


def train_volume_model(db: Session, module: ModuleCode | None = None) -> dict:
    """
    Trains a regressor (XGBoost if PREDICTION_PROVIDER=xgboost and the
    package is installed, else scikit-learn GradientBoostingRegressor) on
    daily complaint counts and saves it to disk. Returns training metrics.
    Raises InsufficientDataError or ImportError on failure — callers decide
    whether to surface that or fall back.
    """
    import joblib
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split

    df = _build_daily_series(db, module)
    X, y, feature_cols, _ = _engineer_features(df)

    if len(X) < MIN_TRAINING_DAYS:
        raise InsufficientDataError(f"Only {len(X)} usable rows after feature engineering.")

    test_size = max(0.15, 3 / len(X))
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)

    model_name = "sklearn_gbr"
    if settings.PREDICTION_PROVIDER == "xgboost":
        try:
            from xgboost import XGBRegressor

            model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
            model_name = "xgboost"
        except ImportError:
            logger.warning("xgboost not installed, falling back to scikit-learn GradientBoostingRegressor for training")
            from sklearn.ensemble import GradientBoostingRegressor

            model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
    else:
        from sklearn.ensemble import GradientBoostingRegressor

        model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)

    model.fit(X_train, y_train)

    metrics = {"model_name": model_name, "training_rows": len(X), "feature_columns": feature_cols}
    if len(X_test) > 0:
        predictions = model.predict(X_test)
        metrics["mae"] = round(float(mean_absolute_error(y_test, predictions)), 3)
        metrics["r2"] = round(float(r2_score(y_test, predictions)), 3) if len(X_test) > 1 else None
    else:
        metrics["mae"] = None
        metrics["r2"] = None

    joblib.dump(
        {"model": model, "feature_columns": feature_cols, "trained_at": datetime.now(timezone.utc).isoformat(), "metrics": metrics},
        _model_path(module),
    )
    logger.info("Trained volume model for module=%s: %s", module.value if module else "all", metrics)
    return metrics


def predict_volume_ml(db: Session, module: ModuleCode | None, days_ahead: int) -> dict:
    """
    Loads (or trains on the fly, if no saved model exists yet) the volume
    model and projects forward. Raises InsufficientDataError/ImportError/
    FileNotFoundError on any failure — dashboard_service.py catches these
    and falls back to the demo heuristic.
    """
    import joblib
    import numpy as np

    path = _model_path(module)
    if not path.exists():
        train_volume_model(db, module)  # train once on first use

    bundle = joblib.load(path)
    model = bundle["model"]
    feature_cols = bundle["feature_columns"]

    df = _build_daily_series(db, module)
    history = df["count"].tolist()
    last_day = df["day"].max()

    points = []
    rolling_window = history[-7:]
    for i in range(1, days_ahead + 1):
        target_date = last_day + timedelta(days=i)
        features = {
            "day_of_week": target_date.dayofweek if hasattr(target_date, "dayofweek") else target_date.weekday(),
            "day_of_month": target_date.day,
            "days_since_start": (target_date - df["day"].min()).days,
            "rolling_7": float(np.mean(rolling_window[-7:])) if rolling_window else 0.0,
            "rolling_3": float(np.mean(rolling_window[-3:])) if rolling_window else 0.0,
        }
        X = [[features[c] for c in feature_cols]]
        predicted = max(0.0, round(float(model.predict(X)[0]), 1))
        points.append({"date": target_date.date().isoformat() if hasattr(target_date, "date") else target_date.isoformat(), "predicted_count": predicted, "module": module.value if module else None})
        rolling_window.append(predicted)

    return {
        "is_demo_data": True,
        "model_name": bundle["metrics"]["model_name"],
        "points": points,
        "note": (
            f"Trained {bundle['metrics']['model_name']} model on {bundle['metrics']['training_rows']} days of "
            f"(seed/demo) complaint history — MAE={bundle['metrics'].get('mae')}, R²={bundle['metrics'].get('r2')}. "
            "This is a real trained model, but the training data is synthetic seed data, not real government "
            "complaint history, so treat the forecast as illustrative rather than production-grade."
        ),
    }


def cluster_hotspots_dbscan(db: Session, module: ModuleCode | None = None, eps_km: float = 1.0, min_samples: int = 3) -> list[dict]:
    """
    DBSCAN clustering on complaint lat/lng — a genuine spatial ML approach
    (as opposed to Part 3's fixed-grid bucketing), used when
    PREDICTION_PROVIDER is 'sklearn' or 'xgboost'. Falls back to the grid
    heuristic (dashboard_service.get_hotspots) on ImportError or if there
    are too few points to cluster meaningfully.
    """
    import numpy as np
    from sklearn.cluster import DBSCAN

    query = db.query(Complaint.latitude, Complaint.longitude, Complaint.module, Complaint.priority).filter(
        Complaint.latitude.isnot(None), Complaint.longitude.isnot(None)
    )
    if module:
        query = query.filter(Complaint.module == module)

    rows = query.all()
    if len(rows) < min_samples:
        raise InsufficientDataError(f"Only {len(rows)} geotagged complaints — need at least {min_samples} to cluster.")

    coords = np.radians([(r[0], r[1]) for r in rows])
    earth_radius_km = 6371.0
    eps_rad = eps_km / earth_radius_km

    labels = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine").fit_predict(coords)

    clusters: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        if label == -1:
            continue  # noise point, not part of any cluster
        clusters.setdefault(label, []).append(idx)

    results = []
    for indices in clusters.values():
        lats = [rows[i][0] for i in indices]
        lngs = [rows[i][1] for i in indices]
        modules_seen = [rows[i][2].value for i in indices]
        priorities_seen = [rows[i][3].value for i in indices]
        results.append({
            "latitude": round(float(np.mean(lats)), 5),
            "longitude": round(float(np.mean(lngs)), 5),
            "count": len(indices),
            "dominant_module": max(set(modules_seen), key=modules_seen.count),
            "dominant_priority": max(set(priorities_seen), key=priorities_seen.count),
        })

    return sorted(results, key=lambda r: r["count"], reverse=True)
