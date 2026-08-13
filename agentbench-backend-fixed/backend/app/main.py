import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.db.init_db import init_db
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.benchmarks import router as benchmark_router
from app.api.agents import router as agents_router
from app.api.tasks import router as tasks_router
from app.api.evaluations import router as evaluations_router
from app.api.task_runner import router as task_runner_router
from app.api.settings import router as settings_router

logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter is defined in app.core.limiter (keyed by client IP) and
# applied to the auth endpoints (see app/api/auth.py) to slow down
# credential-stuffing / brute-force attempts against login and mass
# account creation against register.


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    logger.info("Startup complete (environment=%s).", settings.ENVIRONMENT)
    yield
    # Shutdown - nothing to clean up today, placeholder for future
    # connection-pool / background-task teardown.
    logger.info("Shutting down.")


app = FastAPI(
    title="AgentBench API",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Default FastAPI validation errors are fine for API consumers but can
    # be noisy; keep the shape consistent with the rest of the API's error
    # responses ({"detail": ...}).
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces / internal details to the client. Full detail
    # still goes to the server logs for debugging.
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(benchmark_router)
app.include_router(agents_router)
app.include_router(tasks_router)
app.include_router(evaluations_router)
app.include_router(task_runner_router)
app.include_router(settings_router)


@app.get("/")
def root():
    return {"message": "AgentBench API", "environment": settings.ENVIRONMENT}


@app.get("/health")
def health():
    """Basic liveness endpoint for load balancers / container orchestrators."""
    return {"status": "ok"}
