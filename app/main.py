from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import get_settings
from app.api import auth_router, code_router, agent_routes
import sys
import typing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Bridge IDE - Execute code and GitHub OAuth",
    version="1.0.0",
    debug=settings.DEBUG
)

# Patch ForwardRef._evaluate to be compatible with Python >=3.12.4
if sys.version_info >= (3, 12, 4):
    original_evaluate = typing.ForwardRef._evaluate

    def patched_evaluate(self, globalns, localns, recursive_guard=frozenset()):
        return original_evaluate(self, globalns, localns, recursive_guard=recursive_guard)

    typing.ForwardRef._evaluate = patched_evaluate

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(code_router, prefix=settings.API_V1_STR)
app.include_router(agent_routes.router, prefix=settings.API_V1_STR, tags=["agents"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
