from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.app.api.v1.router import api_router
from backend.app.core.db import engine
from backend.app.models import Base

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to create database tables, but don't fail if DB is not available
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified successfully")
except Exception as e:
    logger.warning(f"Database not available at startup: {e}")
    logger.warning("API will start but database operations will fail")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events για την εφαρμογή."""
    # Startup
    logger.info("Starting MOOCs Aggregator API...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MOOCs Aggregator API...")

app = FastAPI(
    title="MOOCs Aggregator API",
    description="API for aggregating courses from multiple MOOC platforms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite dev server alternative port
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "MOOCs Aggregator API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}