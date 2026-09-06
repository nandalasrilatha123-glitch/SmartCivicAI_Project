from pydantic import BaseModel


class OverviewStats(BaseModel):
    total: int
    new: int
    pending: int
    assigned: int
    in_progress: int
    resolved: int
    rejected: int
    escalated: int
    requires_admin_review: int
    overdue: int          # open >7 days and not resolved/rejected
    high_priority: int    # priority in (HIGH, CRITICAL) and still open


class CountByLabel(BaseModel):
    label: str
    count: int


class TimeSeriesPoint(BaseModel):
    period: str  # ISO date/week/month/year label depending on granularity
    count: int


class ModuleStatusCell(BaseModel):
    module: str
    status: str
    count: int


class DepartmentPerformance(BaseModel):
    department_id: str
    department_name: str
    module: str
    received: int
    resolved: int
    pending: int
    resolution_rate: float  # percentage, 0-100


class ResolutionTimeStats(BaseModel):
    overall_avg_hours: float | None
    by_module: list[dict]  # [{module, avg_hours, resolved_count}]


class AIClassificationStats(BaseModel):
    total_analyzed: int
    avg_module_confidence: float | None
    avg_category_confidence: float | None
    overridden_count: int
    override_rate: float  # percentage
    requires_review_count: int


class AIRoutingStats(BaseModel):
    total_routed: int
    avg_confidence: float | None
    overridden_count: int
    unrouted_count: int  # AI could not find a department


class HotspotPoint(BaseModel):
    latitude: float
    longitude: float
    count: int
    dominant_module: str
    dominant_priority: str


class PredictedVolumePoint(BaseModel):
    date: str
    predicted_count: float
    module: str | None


class PredictedVolumeResponse(BaseModel):
    is_demo_data: bool
    model_name: str
    points: list[PredictedVolumePoint]
    note: str


class PredictedHotspotArea(BaseModel):
    latitude: float
    longitude: float
    risk_score: float  # 0-1, higher = more likely to generate future complaints
    recent_count: int
    module: str | None


class PredictedHotspotsResponse(BaseModel):
    is_demo_data: bool
    model_name: str
    areas: list[PredictedHotspotArea]
    note: str
