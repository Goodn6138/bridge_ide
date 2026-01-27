"""API routes module initialization"""
from .auth import router as auth_router
from .code import router as code_router

__all__ = ["auth_router", "code_router"]
