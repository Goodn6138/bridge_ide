from fastapi import APIRouter, HTTPException
from app.models import CodeExecutionRequest, CodeExecutionResult
from app.services.judge0 import submit_code, get_language_id, format_result
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/code", tags=["code execution"])


@router.post("/execute", response_model=CodeExecutionResult)
async def execute_code(request: CodeExecutionRequest) -> CodeExecutionResult:
    """
    Execute code using Judge0 API.
    
    Args:
        request: CodeExecutionRequest with code and optional language/filename/stdin
        
    Returns:
        CodeExecutionResult with execution output and metadata
    """
    try:
        if not request.code or not isinstance(request.code, str):
            logger.warning("[Code] Execute request received without valid code")
            raise HTTPException(status_code=400, detail="No valid code provided")
        
        # Determine language ID from filename or language parameter
        language_id = get_language_id(request.filename) if request.filename else (
            get_language_id(request.language) if request.language else 71
        )
        
        logger.info(f"[Code] Executing code: filename={request.filename}, "
                   f"language={request.language}, language_id={language_id}, "
                   f"code_length={len(request.code)}")
        
        # Submit code to Judge0
        submission = await submit_code(
            {
                "source_code": request.code,
                "language_id": language_id,
                "stdin": request.stdin or None,
            },
            wait=True
        )
        
        logger.info(f"[Code] Submission result: token={submission.get('token')}, "
                   f"status={submission.get('status', {}).get('description')}")
        
        # Format result for API response
        formatted = format_result(submission)
        
        return CodeExecutionResult(
            success=formatted["success"],
            output=formatted["output"],
            error=formatted["error"],
            stdout=formatted["output"],
            stderr=formatted["error"],
            time=formatted["time"],
            memory=formatted["memory"],
            token=submission.get("token"),
            status=submission.get("status"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Code] Execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported programming languages.
    
    Returns:
        Dict mapping language names to Judge0 language IDs
    """
    from app.services.judge0 import LANGUAGE_ID_MAP
    
    return {
        "supported_languages": LANGUAGE_ID_MAP,
        "default": {"name": "python", "id": 71}
    }
