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

@router.get("/api/preview/stackblitz/{app_id}")
async def get_stackblitz_preview(app_id: str):
    """
    Serve an HTML page that creates a StackBlitz project with the user's files.
    This is used when npm is not available (e.g., Vercel serverless).
    
    Args:
        app_id: Unique app identifier
    
    Returns:
        HTML page with auto-submitting form to create StackBlitz project
    """
    from fastapi.responses import HTMLResponse
    import json
    
    # Load files from stackblitz directory
    stackblitz_dir = PREVIEWS_DIR / app_id / "stackblitz"
    
    if not stackblitz_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"StackBlitz preview not found for app {app_id}"
        )
    
    # Read all files
    files = {}
    for file_path in stackblitz_dir.rglob("*"):
        if file_path.is_file():
            # Get relative path from stackblitz directory
            rel_path = file_path.relative_to(stackblitz_dir)
            try:
                files[str(rel_path).replace("\\", "/")] = file_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
    
    if not files:
        raise HTTPException(
            status_code=404,
            detail=f"No files found for StackBlitz preview {app_id}"
        )
    
    # Create the project data payload
    project_data = {
        "files": files,
        "template": "node",
        "title": f"Bridge IDE - {app_id}",
        "description": "Generated React App Preview"
    }
    
    # Generate HTML with auto-submitting form
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Opening Preview on StackBlitz...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            text-align: center;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            max-width: 500px;
        }}
        h1 {{
            color: #333;
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .rocket {{
            font-size: 48px;
            margin-bottom: 20px;
        }}
        p {{
            color: #666;
            margin: 10px 0;
            font-size: 16px;
            line-height: 1.5;
        }}
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 30px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .button {{
            background: #667eea;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            margin-top: 30px;
            transition: background 0.3s;
        }}
        .button:hover {{
            background: #5568d3;
        }}
        .info {{
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-top: 20px;
            text-align: left;
            border-radius: 4px;
            font-size: 14px;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="rocket">🚀</div>
        <h1>Creating Preview</h1>
        <p>Opening your React app on StackBlitz...</p>
        <div class="spinner"></div>
        <p>If the page doesn't open automatically, click below:</p>
        <form id="stackblitz-form" method="post" action="https://stackblitz.com/api/v1/project" target="_blank">
            <button type="submit" class="button">Open on StackBlitz</button>
        </form>
        <div class="info">
            <strong>What's happening?</strong><br>
            Your code is being sent to StackBlitz where it will be built and previewed in your browser.
        </div>
    </div>
    
    <script>
        // Prepare the project data
        const projectData = {json.dumps(project_data)};
        
        // Set form fields for each file
        const form = document.getElementById('stackblitz-form');
        
        Object.entries(projectData.files).forEach(([filename, content]) => {{
            const input = document.createElement('textarea');
            input.name = 'files[' + filename + ']';
            input.value = content;
            form.appendChild(input);
        }});
        
        // Add other project settings
        const titleInput = document.createElement('input');
        titleInput.type = 'hidden';
        titleInput.name = 'title';
        titleInput.value = projectData.title;
        form.appendChild(titleInput);
        
        const templateInput = document.createElement('input');
        templateInput.type = 'hidden';
        templateInput.name = 'template';
        templateInput.value = projectData.template;
        form.appendChild(templateInput);
        
        const descInput = document.createElement('input');
        descInput.type = 'hidden';
        descInput.name = 'description';
        descInput.value = projectData.description;
        form.appendChild(descInput);
        
        // Auto-submit the form after a short delay
        setTimeout(() => {{
            form.submit();
        }}, 1000);
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html_content)