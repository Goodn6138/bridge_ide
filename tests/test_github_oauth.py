import pytest
from unittest.mock import patch, AsyncMock
from app.services.github_oauth import (
    get_github_access_token,
    get_github_user,
    authenticate_github_user
)
from app.models import GithubUser
import aiohttp


class TestGithubOAuth:
    """Tests for GitHub OAuth service"""
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful access token retrieval"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "access_token": "gho_test_token_123",
            "scope": "user:email",
            "token_type": "bearer"
        })
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            token = await get_github_access_token("test_code_123")
            assert token == "gho_test_token_123"
    
    @pytest.mark.asyncio
    async def test_get_access_token_error_response(self):
        """Test access token retrieval with error in response"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "error": "bad_verification_code",
            "error_description": "The code passed is incorrect or expired."
        })
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await get_github_access_token("invalid_code")
            assert "bad_verification_code" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_access_token_http_error(self):
        """Test access token retrieval with HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await get_github_access_token("test_code")
            assert "401" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_github_user_success(self):
        """Test successful user retrieval"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "id": 123456,
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/123456",
            "html_url": "https://github.com/testuser"
        })
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            user = await get_github_user("test_token_123")
            assert user.login == "testuser"
            assert user.id == 123456
            assert user.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_github_user_http_error(self):
        """Test user retrieval with HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Bad credentials")
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await get_github_user("invalid_token")
            assert "401" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_authenticate_github_user_success(self):
        """Test complete authentication flow"""
        with patch('app.services.github_oauth.get_github_access_token') as mock_token:
            with patch('app.services.github_oauth.get_github_user') as mock_user_fetch:
                expected_user = GithubUser(
                    id=123456,
                    login="testuser",
                    name="Test User",
                    email="test@example.com",
                    avatar_url="https://avatars.githubusercontent.com/u/123456",
                    profile_url="https://github.com/testuser"
                )
                
                mock_token.return_value = "test_token_123"
                mock_user_fetch.return_value = expected_user
                
                user = await authenticate_github_user("test_code")
                assert user.login == "testuser"
                assert user.id == 123456


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
