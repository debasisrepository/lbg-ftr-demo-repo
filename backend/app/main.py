from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth_router
from app.api.my_cases import resolve_router, cases_router
from app.api.my_cases import evidence_router
from app.api.colleague import cases_router as colleague_router
from app.middleware.correlation import CorrelationIdMiddleware
from app.core.logging import logger
from app.events.dispatcher import get_dispatcher
from app.services.heartbeat.scheduler import get_scheduler
from app.services.notification.service import NotificationService


@asynccontextmanager
async def lifespan(app: FastAPI):
    NotificationService.register_handlers()
    dispatcher = get_dispatcher()
    dispatcher.start()
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Background services started")
    yield
    dispatcher.stop()
    scheduler.stop()
    logger.info("Background services stopped")


app = FastAPI(
    title="Clear Path API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(resolve_router.router, prefix="/api/v1")
app.include_router(cases_router.router, prefix="/api/v1")
app.include_router(evidence_router.router, prefix="/api/v1")
app.include_router(colleague_router.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    return {"status": "ready"}


logger.info("Clear Path API initialized")
