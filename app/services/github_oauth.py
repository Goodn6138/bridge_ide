import aiohttp
import logging
from typing import Optional, Dict, Any
from app.core.config import get_settings
from app.models import GithubUser

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_github_access_token(code: str) -> str:
    """
    Exchange GitHub authorization code for access token.
    
    Args:
        code: Authorization code from GitHub callback
        
    Returns:
        Access token string
        
    Raises:
        Exception: If token exchange fails
    """
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }
    
    headers = {"Accept": "application/json"}
    
    logger.info("[GitHub] Exchanging authorization code for access token")
    
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                "https://github.com/login/oauth/access_token",
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            )
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"[GitHub] Token exchange error {response.status}: {error_text}")
                raise Exception(f"GitHub token exchange failed: {response.status}")

            result = await response.json()

            if "error" in result:
                logger.error(f"[GitHub] Error in response: {result.get('error_description')}")
                raise Exception(f"GitHub error: {result.get('error_description')}")

            token = result.get("access_token")
            if not token:
                raise Exception("No access token in GitHub response")

            logger.info("[GitHub] Successfully obtained access token")
            return token
    except aiohttp.ClientError as e:
        logger.error(f"[GitHub] Connection error: {str(e)}")
        raise Exception(f"GitHub connection error: {str(e)}")


async def get_github_user(access_token: str) -> GithubUser:
    """
    Fetch GitHub user information using access token.
    
    Args:
        access_token: GitHub OAuth access token
        
    Returns:
        GithubUser model with user information
        
    Raises:
        Exception: If user fetch fails
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    
    logger.info("[GitHub] Fetching user information")
    
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            )
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"[GitHub] User fetch error {response.status}: {error_text}")
                raise Exception(f"GitHub user fetch failed: {response.status}")

            user_data = await response.json()

            logger.info(f"[GitHub] Successfully fetched user: {user_data.get('login')}")

            return GithubUser(
                id=user_data.get("id"),
                login=user_data.get("login"),
                name=user_data.get("name"),
                email=user_data.get("email"),
                avatar_url=user_data.get("avatar_url"),
                profile_url=user_data.get("html_url"),
            )
    except aiohttp.ClientError as e:
        logger.error(f"[GitHub] Connection error: {str(e)}")
        raise Exception(f"GitHub connection error: {str(e)}")


async def authenticate_github_user(code: str) -> GithubUser:
    """
    Complete GitHub OAuth flow: exchange code for token and fetch user.
    
    Args:
        code: Authorization code from GitHub callback
        
    Returns:
        GithubUser model
        
    Raises:
        Exception: If authentication fails
    """
    try:
        access_token = await get_github_access_token(code)
        user = await get_github_user(access_token)
        logger.info(f"[GitHub] Authentication successful for user: {user.login}")
        return user
    except Exception as e:
        logger.error(f"[GitHub] Authentication failed: {str(e)}")
        raise
