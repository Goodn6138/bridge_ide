from fastapi import APIRouter, HTTPException
from app.models import GithubAuthRequest, AuthResponse
from app.services.github_oauth import authenticate_github_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github/login")
async def github_login():
    """
    Redirect user to GitHub OAuth login page.
    
    Returns:
        Redirect URL to GitHub OAuth authorization endpoint
    """
    from app.core.config import get_settings
    settings = get_settings()
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
        f"&state=bridge-ide"
    )
    
    return {"login_url": github_auth_url}


@router.post("/github/callback")
async def github_callback(request: GithubAuthRequest) -> AuthResponse:
    """
    Handle GitHub OAuth callback and authenticate user.
    
    Args:
        request: Contains the authorization code from GitHub
        
    Returns:
        AuthResponse with user information and success status
    """
    try:
        if not request.code:
            logger.warning("[Auth] GitHub callback received without code")
            raise HTTPException(status_code=400, detail="Authorization code is required")
        
        logger.info("[Auth] Processing GitHub callback")
        user = await authenticate_github_user(request.code)
        
        # In production, you would generate a JWT token here
        return AuthResponse(
            success=True,
            user=user,
            token=f"github-{user.id}",  # Placeholder - implement proper JWT
        )
    except Exception as e:
        logger.error(f"[Auth] GitHub callback failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/github/user")
async def get_current_user():
    """
    Get currently authenticated user information.
    In production, extract from JWT token.
    """
    return {
        "message": "Implement token verification and return current user",
        "note": "Add JWT token verification middleware in production"
    }
