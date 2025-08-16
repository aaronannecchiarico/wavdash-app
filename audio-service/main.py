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
from routes.audio_processing import router as audio_router
from routes.storage import router as storage_router
from routes.tasks import router as tasks_router
from routes.health import router as health_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting audio processing microservice")
    yield
    logging.info("Shutting down audio processing microservice")


app = FastAPI(
    title="Audio Processing Microservice",
    description="FastAPI microservice for audio feature extraction and stem separation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(health_router)
app.include_router(audio_router)
app.include_router(storage_router)
app.include_router(tasks_router)
app.include_router(tempo_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed logging"""
    request_body = None
    try:
        request_body = await request.body()
        if request_body:
            request_body = request_body.decode('utf-8')
    except Exception:
        request_body = "Unable to read request body"
    
    logging.error(f"422 Validation Error on {request.method} {request.url}")
    logging.error(f"Request body: {request_body}")
    logging.error(f"Validation errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": request_body if request_body != "Unable to read request body" else None
        }
    )




if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )