import aiohttp
import logging
from typing import Optional, Dict, Any
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Judge0 Language ID mapping
LANGUAGE_ID_MAP = {
    "python": 71,
    "python3": 71,
    "py": 71,
    "javascript": 63,
    "js": 63,
    "typescript": 74,
    "ts": 74,
    "java": 62,
    "cpp": 54,
    "c": 50,
    "csharp": 51,
    "c#": 51,
    "ruby": 72,
    "go": 60,
    "rust": 73,
    "php": 68,
    "swift": 85,
    "kotlin": 78,
    "r": 80,
    "bash": 46,
    "shell": 46,
    "sql": 82,
}


def get_language_id(filename_or_language: str) -> int:
    """
    Determine language ID from filename or language name.
    Returns Python 3 (71) as default.
    """
    if not filename_or_language:
        return 71  # Python 3 default
    
    identifier = filename_or_language.lower().strip()
    
    # Try direct mapping first
    if identifier in LANGUAGE_ID_MAP:
        return LANGUAGE_ID_MAP[identifier]
    
    # Try file extension
    if "." in identifier:
        ext = identifier.split(".")[-1].lower()
        if ext in LANGUAGE_ID_MAP:
            return LANGUAGE_ID_MAP[ext]
    
    # Default to Python 3
    logger.warning(f"Unknown language/file: {filename_or_language}, defaulting to Python 3")
    return 71


async def submit_code(
    code_data: Dict[str, Any],
    wait: bool = True,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Submit code to Judge0 API for execution.
    
    Args:
        code_data: Dict with source_code, language_id, and optional stdin
        wait: If True, wait for execution result
        timeout: Timeout in seconds for the request
        
    Returns:
        Submission result from Judge0
        
    Raises:
        Exception: If API call fails
    """
    headers = {
        "x-rapidapi-key": settings.JUDGE0_API_KEY,
        "x-rapidapi-host": settings.JUDGE0_API_HOST,
        "Content-Type": "application/json"
    }
    
    params = {"wait": "true" if wait else "false"}
    
    logger.info(f"[Judge0] Submitting code: language_id={code_data.get('language_id')}, "
                f"code_length={len(code_data.get('source_code', ''))}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.JUDGE0_API_URL}/submissions",
                json=code_data,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 201:
                    error_text = await response.text()
                    logger.error(f"[Judge0] API error {response.status}: {error_text}")
                    raise Exception(f"Judge0 API error: {response.status} - {error_text}")
                
                result = await response.json()
                logger.info(f"[Judge0] Submission successful: token={result.get('token')}")
                return result
    except aiohttp.ClientError as e:
        logger.error(f"[Judge0] Connection error: {str(e)}")
        raise Exception(f"Judge0 connection error: {str(e)}")


def format_result(submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format Judge0 submission result for API response.
    
    Args:
        submission: Result dict from Judge0
        
    Returns:
        Formatted result dict
    """
    status = submission.get("status", {})
    status_id = status.get("id", 0)
    status_desc = status.get("description", "Unknown")
    
    # Status ID: 1=In Queue, 2=Processing, 3=Accepted, 4=Wrong Answer, 
    #            5=Time Limit, 6=Compilation Error, 7=Runtime Error, etc.
    is_success = status_id == 3
    
    output = submission.get("stdout", "") or ""
    error = submission.get("stderr", "") or submission.get("compile_output", "") or ""
    
    if not is_success and error:
        output = error
    
    return {
        "success": is_success,
        "output": output,
        "error": error if not is_success else None,
        "time": submission.get("time"),
        "memory": submission.get("memory"),
    }
