"""API module initialization"""
from .routes import auth_router, code_router

# Lazy import agent_routes to avoid loading langgraph on startup
def get_agent_routes():
    from . import agent_routes
    return agent_routes

__all__ = ["auth_router", "code_router", "get_agent_routes"]
