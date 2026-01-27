import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.models import GithubUser
import json


@pytest.fixture
async def client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestAuthRoutes:
    """Tests for GitHub authentication routes"""
    
    @pytest.mark.asyncio
    async def test_github_login_url(self, client):
        """Test GitHub login URL generation"""
        response = await client.get("/api/auth/github/login")
        assert response.status_code == 200
        data = response.json()
        assert "login_url" in data
        assert "https://github.com/login/oauth/authorize" in data["login_url"]
        assert "client_id" in data["login_url"]
        assert "redirect_uri" in data["login_url"]
    
    @pytest.mark.asyncio
    async def test_github_callback_missing_code(self, client):
        """Test GitHub callback with missing code"""
        response = await client.post(
            "/api/auth/github/callback",
            json={"code": ""}
        )
        assert response.status_code == 400
        assert "Authorization code is required" in response.text
    
    @pytest.mark.asyncio
    async def test_github_callback_success(self, client):
        """Test successful GitHub callback"""
        mock_user = GithubUser(
            id=123456,
            login="testuser",
            name="Test User",
            email="test@example.com",
            avatar_url="https://avatars.githubusercontent.com/u/123456",
            profile_url="https://github.com/testuser"
        )
        
        with patch('app.services.github_oauth.authenticate_github_user') as mock_auth:
            mock_auth.return_value = mock_user
            
            response = await client.post(
                "/api/auth/github/callback",
                json={"code": "test_code_123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user"]["login"] == "testuser"
            assert data["user"]["id"] == 123456
            assert data["token"] is not None
    
    @pytest.mark.asyncio
    async def test_github_callback_failure(self, client):
        """Test GitHub callback with authentication failure"""
        with patch('app.services.github_oauth.authenticate_github_user') as mock_auth:
            mock_auth.side_effect = Exception("GitHub API error")
            
            response = await client.post(
                "/api/auth/github/callback",
                json={"code": "invalid_code"}
            )
            
            assert response.status_code == 401
            assert "GitHub API error" in response.text
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client):
        """Test get current user endpoint"""
        response = await client.get("/api/auth/github/user")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestCodeExecutionRoutes:
    """Tests for code execution routes"""
    
    @pytest.mark.asyncio
    async def test_get_supported_languages(self, client):
        """Test getting supported languages"""
        response = await client.get("/api/code/languages")
        assert response.status_code == 200
        data = response.json()
        assert "supported_languages" in data
        assert "default" in data
        assert data["supported_languages"]["python"] == 71
        assert data["default"]["id"] == 71
    
    @pytest.mark.asyncio
    async def test_execute_code_missing_code(self, client):
        """Test code execution with missing code"""
        response = await client.post(
            "/api/code/execute",
            json={"code": ""}
        )
        assert response.status_code == 400
        assert "No valid code provided" in response.text
    
    @pytest.mark.asyncio
    async def test_execute_code_success(self, client):
        """Test successful code execution"""
        mock_submission = {
            "token": "test_token_123",
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "Hello, World!\n",
            "stderr": None,
            "time": 0.123,
            "memory": 12345,
        }
        
        with patch('app.services.judge0.submit_code') as mock_submit:
            mock_submit.return_value = mock_submission
            
            response = await client.post(
                "/api/code/execute",
                json={
                    "code": "print('Hello, World!')",
                    "language": "python",
                    "stdin": None
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Hello, World!" in data["output"]
            assert data["token"] == "test_token_123"
            assert data["time"] == 0.123
    
    @pytest.mark.asyncio
    async def test_execute_code_with_filename(self, client):
        """Test code execution with filename-based language detection"""
        mock_submission = {
            "token": "test_token_456",
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "42\n",
            "time": 0.05,
            "memory": 8000,
        }
        
        with patch('app.services.judge0.submit_code') as mock_submit:
            mock_submit.return_value = mock_submission
            
            response = await client.post(
                "/api/code/execute",
                json={
                    "code": "puts 42",
                    "filename": "solution.rb"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_code_with_stdin(self, client):
        """Test code execution with stdin"""
        mock_submission = {
            "token": "test_token_789",
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "Input was: hello\n",
            "time": 0.05,
            "memory": 8000,
        }
        
        with patch('app.services.judge0.submit_code') as mock_submit:
            mock_submit.return_value = mock_submission
            
            response = await client.post(
                "/api/code/execute",
                json={
                    "code": "input_val = input()\nprint(f'Input was: {input_val}')",
                    "language": "python",
                    "stdin": "hello"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_code_runtime_error(self, client):
        """Test code execution with runtime error"""
        mock_submission = {
            "token": "test_token_error",
            "status": {"id": 7, "description": "Runtime Error"},
            "stdout": None,
            "stderr": "ZeroDivisionError: division by zero",
            "time": 0.01,
            "memory": 5000,
        }
        
        with patch('app.services.judge0.submit_code') as mock_submit:
            mock_submit.return_value = mock_submission
            
            response = await client.post(
                "/api/code/execute",
                json={
                    "code": "x = 1 / 0",
                    "language": "python"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "ZeroDivisionError" in data["error"]
    
    @pytest.mark.asyncio
    async def test_execute_code_compilation_error(self, client):
        """Test code execution with compilation error"""
        mock_submission = {
            "token": "test_token_compile",
            "status": {"id": 6, "description": "Compilation Error"},
            "stdout": None,
            "stderr": "error: unexpected token",
            "compile_output": "error: unexpected token",
            "time": None,
            "memory": None,
        }
        
        with patch('app.services.judge0.submit_code') as mock_submit:
            mock_submit.return_value = mock_submission
            
            response = await client.post(
                "/api/code/execute",
                json={
                    "code": "this is not valid syntax !!!!!",
                    "language": "python"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Bridge IDE" in data["message"]
        assert "docs" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
