from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

from .config import settings
from .database import engine, Base, get_db
from .routers import (
    auth_router,
    patients_router,
    upload_router,
    viewer_router,
    wearables_router
)
from .utils.s3 import S3Service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="QAS AI Medical Data Management System",
    description="Comprehensive healthcare data management platform with DICOM viewer, OCR, and wearable integration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting up QAS AI Medical System...")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    # Initialize S3 bucket
    try:
        s3_service = S3Service()
        s3_service.create_bucket_if_not_exists()
        logger.info("S3 bucket initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing S3 bucket: {e}")

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down QAS AI Medical System...")


# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "QAS AI Medical Data Management System API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify system status"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "api": "operational"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Include routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(upload_router)
app.include_router(viewer_router)
app.include_router(wearables_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    logger.error(f"Global exception: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please contact support."
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
