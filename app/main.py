import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import TaskNotFoundError
from app.core.logging_config import configure_logging
from app.routers import tasks

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


app = FastAPI(title="Tasks API", version="0.1.0", lifespan=lifespan)

app.include_router(tasks.router)


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(
    request: Request, exc: TaskNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # CRITICAL: never let a raw 500 + stack trace reach the client.
    # That stack trace can leak file paths, library versions, even
    # query strings. Log full detail server-side, return a generic
    # message client-side.
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    """
    Liveness probe. nginx and Docker's healthcheck both hit this.
    Keep it dependency-free and fast — don't query a DB here unless
    you specifically want a 'readiness' check that fails on DB outage.
    """
    return {"status": "ok"}

@app.get("/version")
async def version():
    return {"version": "1.0.0", "service": "tasks-api"}
