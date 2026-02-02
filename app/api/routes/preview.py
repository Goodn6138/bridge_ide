"""
Preview routes for serving generated React apps.
Handles preview uploads, serving static files, and deletion.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import base64
import logging
from datetime import datetime

from app.services.cleanup import (
    ensure_previews_dir,
    extract_tar_gz,
    validate_preview_structure,
    cleanup_preview_by_id,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Use /tmp for serverless (Vercel) - filesystem is ephemeral
PREVIEWS_DIR = Path("/tmp/previews")


@router.post("/api/preview/upload/{app_id}")
async def upload_preview(
    app_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload dist.tar.gz for a generated app and extract to preview directory.
    
    Args:
        app_id: Unique app identifier
        file: dist.tar.gz file (tar.gz archive)
    
    Returns:
        JSON with upload status and preview URL
    """
    ensure_previews_dir()
    
    # Validate file is tar.gz
    if not file.filename.endswith(".tar.gz"):
        raise HTTPException(
            status_code=400,
            detail="File must be a .tar.gz archive"
        )
    
    try:
        # Create preview directory for this app
        preview_path = PREVIEWS_DIR / app_id
        preview_path.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file temporarily
        temp_tar = preview_path / "dist.tar.gz"
        content = await file.read()
        temp_tar.write_bytes(content)
        
        logger.info(f"Received {temp_tar.stat().st_size} bytes for {app_id}")
        
        # Extract tar.gz
        if not extract_tar_gz(temp_tar, preview_path):
            raise Exception("Failed to extract tar.gz")
        
        # Move dist/ to proper location if needed
        # Judge0 output may be nested; handle both cases:
        # Case 1: dist/ is already at preview_path/dist/
        # Case 2: dist/ is nested in preview_path/dist/dist/ (double nesting)
        dist_dir = preview_path / "dist"
        nested_dist = dist_dir / "dist"
        
        if nested_dist.exists() and nested_dist.is_dir():
            # Move nested dist up
            import shutil
            shutil.rmtree(dist_dir)
            nested_dist.parent.rename(dist_dir)
        
        # Validate structure
        if not validate_preview_structure(preview_path):
            logger.warning(f"Preview structure validation failed for {app_id}")
            # Continue anyway - might have different structure
        
        # Clean up temporary tar
        temp_tar.unlink()
        
        # Clean up temporary tar in background after response
        background_tasks.add_task(_cleanup_temp_tar, temp_tar)
        
        preview_url = f"/preview/{app_id}/dist/index.html"
        
        logger.info(f"✅ Preview ready at {preview_url}")
        
        return {
            "success": True,
            "app_id": app_id,
            "preview_url": preview_url,
            "message": "Preview uploaded and extracted successfully"
        }
    
    except Exception as e:
        logger.error(f"Preview upload error for {app_id}: {e}")
        # Cleanup on error
        cleanup_preview_by_id(app_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process preview: {str(e)}"
        )


@router.post("/api/preview/upload-base64/{app_id}")
async def upload_preview_base64(
    app_id: str,
    data: dict,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload base64-encoded dist.tar.gz (from Judge0 build output).
    
    Args:
        app_id: Unique app identifier
        data: JSON with 'archive_b64' (base64 encoded tar.gz)
    
    Returns:
        JSON with upload status and preview URL
    """
    ensure_previews_dir()
    
    try:
        archive_b64 = data.get("archive_b64")
        if not archive_b64:
            raise HTTPException(
                status_code=400,
                detail="Missing 'archive_b64' in request body"
            )
        
        # Create preview directory
        preview_path = PREVIEWS_DIR / app_id
        preview_path.mkdir(parents=True, exist_ok=True)
        
        # Decode base64
        archive_bytes = base64.b64decode(archive_b64)
        temp_tar = preview_path / "dist.tar.gz"
        temp_tar.write_bytes(archive_bytes)
        
        logger.info(f"Received {len(archive_bytes)} bytes (base64) for {app_id}")
        
        # Extract
        if not extract_tar_gz(temp_tar, preview_path):
            raise Exception("Failed to extract tar.gz")
        
        # Handle nested dist
        dist_dir = preview_path / "dist"
        nested_dist = dist_dir / "dist"
        if nested_dist.exists():
            import shutil
            shutil.rmtree(dist_dir)
            nested_dist.parent.rename(dist_dir)
        
        # Validate
        if not validate_preview_structure(preview_path):
            logger.warning(f"Structure validation failed for {app_id}")
        
        # Cleanup temp tar
        temp_tar.unlink()
        background_tasks.add_task(_cleanup_temp_tar, temp_tar)
        
        preview_url = f"/preview/{app_id}/dist/index.html"
        
        logger.info(f"✅ Preview (base64) ready at {preview_url}")
        
        return {
            "success": True,
            "app_id": app_id,
            "preview_url": preview_url,
            "message": "Base64 preview extracted successfully"
        }
    
    except Exception as e:
        logger.error(f"Base64 preview upload error for {app_id}: {e}")
        cleanup_preview_by_id(app_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process base64 preview: {str(e)}"
        )


@router.delete("/api/preview/{app_id}")
async def delete_preview(app_id: str):
    """
    Manually delete a preview directory.
    
    Args:
        app_id: App identifier to delete
    
    Returns:
        JSON with deletion status
    """
    try:
        success = cleanup_preview_by_id(app_id)
        
        if success:
            logger.info(f"Deleted preview for {app_id}")
            return {
                "success": True,
                "message": f"Preview {app_id} deleted"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Preview {app_id} not found"
            )
    
    except Exception as e:
        logger.error(f"Delete preview error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete preview: {str(e)}"
        )


@router.get("/api/preview/status/{app_id}")
async def preview_status(app_id: str):
    """
    Check if preview exists and is valid.
    
    Args:
        app_id: App identifier
    
    Returns:
        JSON with status and preview URL if exists
    """
    ensure_previews_dir()
    preview_path = PREVIEWS_DIR / app_id
    
    if preview_path.exists() and preview_path.is_dir():
        dist_dir = preview_path / "dist"
        index_html = dist_dir / "index.html"
        
        is_valid = index_html.exists()
        
        return {
            "exists": True,
            "valid": is_valid,
            "app_id": app_id,
            "preview_url": f"/preview/{app_id}/dist/index.html" if is_valid else None
        }
    else:
        return {
            "exists": False,
            "valid": False,
            "app_id": app_id,
            "preview_url": None
        }


def _cleanup_temp_tar(tar_path: Path):
    """Helper to cleanup temporary tar file."""
    try:
        if tar_path.exists():
            tar_path.unlink()
            logger.info(f"Cleaned up temporary tar: {tar_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup temp tar: {e}")
