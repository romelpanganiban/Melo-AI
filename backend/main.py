from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status

from api.health import router as health_router
from api.chat import router as chat_router
from api.session import router as session_router
from api.settings import router as settings_router
from api.document import router as document_router
from api.code_analysis import router as code_analysis_router
from api.training import router as training_router
from core.errors import MeloAIException
from core.settings import settings
from core.logging import logger
from database import init_database

# Ensure data directory exists
settings.ensure_data_dir()

# Initialize database
try:
    init_database()
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

app = FastAPI(
    title="Melo-AI",
    version="0.1.0",
    description="Local-first AI assistant with persistent memory"
)

# Global error handler for MeloAIException
@app.exception_handler(MeloAIException)
async def melo_exception_handler(request: Request, exc: MeloAIException):
    """Handle all MeloAI exceptions with proper error responses"""
    logger.error(
        f"MeloAI Error: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        }
    )

# Global error handler for unexpected exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "path": str(request.url.path),
            "exception_type": type(exc).__name__
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {}
        }
    )

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(session_router)
app.include_router(settings_router)
app.include_router(document_router)
app.include_router(code_analysis_router)
app.include_router(training_router)

@app.get("/")
def home():
    return {
        "name": "Melo-AI",
        "status": "running",
        "version": "0.1.0"
    }

# Configure CORS middleware when enabled.
if settings.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )