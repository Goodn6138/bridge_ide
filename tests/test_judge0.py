import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.judge0 import (
    get_language_id,
    submit_code,
    format_result,
    LANGUAGE_ID_MAP
)
import aiohttp


class TestLanguageDetection:
    """Tests for language ID detection"""
    
    def test_language_detection_by_name(self):
        """Test language detection by language name"""
        assert get_language_id("python") == 71
        assert get_language_id("javascript") == 63
        assert get_language_id("java") == 62
        assert get_language_id("cpp") == 54
        assert get_language_id("ruby") == 72
    
    def test_language_detection_by_extension(self):
        """Test language detection by file extension"""
        assert get_language_id("solution.py") == 71
        assert get_language_id("app.js") == 63
        assert get_language_id("Main.java") == 62
        assert get_language_id("code.cpp") == 54
        assert get_language_id("script.rb") == 72
    
    def test_language_detection_case_insensitive(self):
        """Test case-insensitive language detection"""
        assert get_language_id("PYTHON") == 71
        assert get_language_id("JavaScript") == 63
        assert get_language_id("SOLUTION.PY") == 71
    
    def test_language_detection_unknown_defaults_to_python(self):
        """Test unknown language defaults to Python 3"""
        assert get_language_id("unknown_lang") == 71
        assert get_language_id("") == 71
        assert get_language_id(None) == 71
    
    def test_all_language_ids_valid(self):
        """Test that all language IDs are positive integers"""
        for lang, lang_id in LANGUAGE_ID_MAP.items():
            assert isinstance(lang_id, int)
            assert lang_id > 0


class TestCodeSubmission:
    """Tests for code submission to Judge0"""
    
    @pytest.mark.asyncio
    async def test_submit_code_success(self):
        """Test successful code submission"""
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={
            "token": "test_token_123",
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "Hello, World!\n",
            "time": 0.123,
            "memory": 12345,
        })
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await submit_code({
                "source_code": "print('Hello, World!')",
                "language_id": 71,
            })
            
            assert result["token"] == "test_token_123"
            assert result["status"]["id"] == 3
    
    @pytest.mark.asyncio
    async def test_submit_code_api_error(self):
        """Test code submission with API error"""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad request")
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await submit_code({
                    "source_code": "invalid",
                    "language_id": 71,
                })
            assert "400" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_submit_code_connection_error(self):
        """Test code submission with connection error"""
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await submit_code({
                    "source_code": "code",
                    "language_id": 71,
                })
            assert "connection error" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_submit_code_with_stdin(self):
        """Test code submission with stdin"""
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={
            "token": "test_token_stdin",
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "Input: hello\n",
        })
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await submit_code({
                "source_code": "print(input())",
                "language_id": 71,
                "stdin": "hello",
            })
            
            assert result["token"] == "test_token_stdin"


class TestResultFormatting:
    """Tests for result formatting"""
    
    def test_format_result_accepted(self):
        """Test formatting accepted result"""
        submission = {
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "Hello, World!\n",
            "stderr": None,
            "time": 0.123,
            "memory": 12345,
        }
        
        result = format_result(submission)
        assert result["success"] is True
        assert "Hello, World!" in result["output"]
        assert result["error"] is None
        assert result["time"] == 0.123
        assert result["memory"] == 12345
    
    def test_format_result_runtime_error(self):
        """Test formatting runtime error result"""
        submission = {
            "status": {"id": 7, "description": "Runtime Error"},
            "stdout": None,
            "stderr": "ZeroDivisionError: division by zero",
            "time": 0.05,
            "memory": 5000,
        }
        
        result = format_result(submission)
        assert result["success"] is False
        assert "ZeroDivisionError" in result["error"]
    
    def test_format_result_compilation_error(self):
        """Test formatting compilation error result"""
        submission = {
            "status": {"id": 6, "description": "Compilation Error"},
            "stdout": None,
            "stderr": None,
            "compile_output": "syntax error on line 1",
            "time": None,
            "memory": None,
        }
        
        result = format_result(submission)
        assert result["success"] is False
        assert "syntax error" in result["error"]
    
    def test_format_result_wrong_answer(self):
        """Test formatting wrong answer result"""
        submission = {
            "status": {"id": 4, "description": "Wrong Answer"},
            "stdout": "42\n",
            "stderr": None,
            "time": 0.1,
            "memory": 8000,
        }
        
        result = format_result(submission)
        assert result["success"] is False
        assert result["output"] == "42\n"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
