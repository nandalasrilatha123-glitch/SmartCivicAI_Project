import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.analytics import router as analytics_router
from app.api.routes.audit_logs import router as audit_logs_router
from app.api.routes.auth import router as auth_router
from app.api.routes.complaints import router as complaints_router
from app.api.routes.departments import router as departments_router
from app.api.routes.modules import router as modules_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.users import router as users_router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("smartcivicai")
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
# Third-party libraries (e.g. python-multipart) are extremely chatty at
# DEBUG level and would otherwise flood the logs with raw byte-range
# tracing on every file upload. Keep DEBUG scoped to our own app logger.
logging.getLogger("python_multipart").setLevel(logging.WARNING)
logging.getLogger("multipart").setLevel(logging.WARNING)

app = FastAPI(
    title="SmartCivicAI API",
    description=(
        "AI-Powered Smart Civic/Government Complaint Management and "
        "Predictive Analytics Platform — REST API"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error. Please try again later."},
    )


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "env": settings.APP_ENV,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(departments_router, prefix=settings.API_V1_PREFIX)
app.include_router(modules_router, prefix=settings.API_V1_PREFIX)
app.include_router(complaints_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_logs_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)

# Additional routers (predictions training, gis) are added in subsequent
# build parts and included here the same way.
