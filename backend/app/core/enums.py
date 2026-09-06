"""
Shared enumerations. Kept as plain Python str-Enums so they serialize
cleanly through Pydantic and store as VARCHAR (via SQLAlchemy Enum) in
Postgres, which keeps Alembic migrations simple when values are added.
"""
import enum


class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    OFFICER = "OFFICER"
    ADMIN = "ADMIN"


class ModuleCode(str, enum.Enum):
    GOVERNMENT_SCHOOLS = "GOVERNMENT_SCHOOLS"
    AGRICULTURE = "AGRICULTURE"
    HEALTHCARE = "HEALTHCARE"
    TRAFFIC = "TRAFFIC"


class ComplaintStatus(str, enum.Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    REQUIRES_ADMIN_REVIEW = "REQUIRES_ADMIN_REVIEW"


class PriorityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LanguageCode(str, enum.Enum):
    EN = "en"
    TE = "te"
    HI = "hi"


class NotificationType(str, enum.Enum):
    NEW_COMPLAINT = "NEW_COMPLAINT"
    COMPLAINT_ASSIGNED = "COMPLAINT_ASSIGNED"
    STATUS_CHANGED = "STATUS_CHANGED"
    COMPLAINT_RESOLVED = "COMPLAINT_RESOLVED"
    COMPLAINT_ESCALATED = "COMPLAINT_ESCALATED"
    ADMIN_REVIEW_REQUIRED = "ADMIN_REVIEW_REQUIRED"


class ImageAnalysisStatus(str, enum.Enum):
    NOT_ANALYZED = "NOT_ANALYZED"
    PENDING = "PENDING"
    ANALYZED_DEMO = "ANALYZED_DEMO"
    ANALYZED_MODEL = "ANALYZED_MODEL"
    FAILED = "FAILED"


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    AI_OVERRIDE_MODULE = "AI_OVERRIDE_MODULE"
    AI_OVERRIDE_CATEGORY = "AI_OVERRIDE_CATEGORY"
    AI_OVERRIDE_PRIORITY = "AI_OVERRIDE_PRIORITY"
    AI_OVERRIDE_DEPARTMENT = "AI_OVERRIDE_DEPARTMENT"
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
