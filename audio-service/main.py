from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from config import settings
from celery_app import celery_app
from routes.tempo_processing import router as tempo_router
from routes.storage import router as storage_router
from routes.tasks import router as tasks_router
from routes.health import router as health_router
from routes.migration import router as migration_router
from utils.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting audio processing microservice")
    yield
    logging.info("Shutting down audio processing microservice")


app = FastAPI(
    title="Audio Processing Microservice",
    description="FastAPI microservice for audio feature extraction and stem separation",
    version="1.0.0",
    lifespan=lifespan,
)

# Register custom exception handlers
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(health_router)
app.include_router(storage_router)
app.include_router(tasks_router)
app.include_router(tempo_router)

# Only include migration router in development/debug mode
if settings.DEBUG:
    app.include_router(migration_router)
    logging.info("🔧 Migration endpoints enabled (DEBUG=true)")
else:
    logging.info("🔒 Migration endpoints disabled (production mode)")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
