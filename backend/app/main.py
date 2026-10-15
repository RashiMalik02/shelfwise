import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .metrics import register_inventory_collector
from .routers import insights, products

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema is owned by Alembic (run in the container entrypoint), not by the app.
    register_inventory_collector()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Inventory and stock-movement API for the Shelfwise dashboard.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator(
    excluded_handlers=["/metrics", "/health", "/ready"],
    should_group_status_codes=False,
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(products.router)
app.include_router(insights.router)


@app.get("/", tags=["system"])
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health", tags=["system"])
def health():
    """Liveness: the process is up and serving HTTP. Deliberately does not touch the DB."""
    return {"status": "UP"}


@app.get("/ready", tags=["system"])
def ready(db: Session = Depends(get_db)):
    """Readiness: only send traffic here once the database answers."""
    try:
        db.execute(text("SELECT 1 FROM products LIMIT 1"))
    except SQLAlchemyError as exc:
        return JSONResponse(status_code=503, content={"status": "NOT_READY", "reason": exc.__class__.__name__})
    return {"status": "READY"}
