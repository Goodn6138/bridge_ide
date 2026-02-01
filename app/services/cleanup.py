"""
Cleanup service for managing preview file expiration and disk space.
Removes expired preview directories based on timestamps.
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

PREVIEWS_DIR = Path("./previews")


def ensure_previews_dir():
    """Ensure previews directory exists."""
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)


def cleanup_expired_previews(active_projects: Dict[str, dict], expire_hours: int = 24) -> Dict[str, any]:
    """
    Remove preview directories for projects that have expired.
    
    Args:
        active_projects: Dict of project_id -> project metadata (must contain 'expires_at')
        expire_hours: Hours until preview expiration (default 24)
    
    Returns:
        Dict with cleanup stats: {cleaned_count, freed_space_mb, errors}
    """
    ensure_previews_dir()
    
    current_time = datetime.now()
    cleaned_count = 0
    freed_space_mb = 0
    errors = []
    
    try:
        # Check each preview directory
        for preview_dir in PREVIEWS_DIR.iterdir():
            if not preview_dir.is_dir():
                continue
            
            app_id = preview_dir.name
            
            # Check if project exists and is expired
            if app_id in active_projects:
                project = active_projects[app_id]
                expires_at = project.get("expires_at")
                
                if expires_at and isinstance(expires_at, datetime):
                    if current_time > expires_at:
                        # Project is expired, remove it
                        if _remove_preview_dir(preview_dir):
                            cleaned_count += 1
                            freed_space_mb += _get_dir_size_mb(preview_dir)
                            logger.info(f"Cleaned expired preview: {app_id}")
            else:
                # Project not in active list, remove orphaned preview
                if _remove_preview_dir(preview_dir):
                    cleaned_count += 1
                    freed_space_mb += _get_dir_size_mb(preview_dir)
                    logger.info(f"Removed orphaned preview: {app_id}")
    
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        errors.append(str(e))
    
    return {
        "cleaned_count": cleaned_count,
        "freed_space_mb": round(freed_space_mb, 2),
        "errors": errors
    }


def cleanup_preview_by_id(app_id: str) -> bool:
    """
    Manually delete a specific preview directory.
    
    Args:
        app_id: Project ID to clean up
    
    Returns:
        True if successfully deleted, False otherwise
    """
    ensure_previews_dir()
    preview_path = PREVIEWS_DIR / app_id
    return _remove_preview_dir(preview_path)


def extract_tar_gz(tar_path: Path, extract_to: Path) -> bool:
    """
    Extract tar.gz build artifact to preview directory.
    
    Args:
        tar_path: Path to dist.tar.gz file
        extract_to: Directory to extract into
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import tarfile
        
        extract_to.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=extract_to)
        
        logger.info(f"Extracted {tar_path.name} to {extract_to}")
        return True
    
    except Exception as e:
        logger.error(f"Error extracting tar.gz: {e}")
        return False


def validate_preview_structure(preview_path: Path) -> bool:
    """
    Validate that extracted preview has required structure.
    Should contain dist/ directory with index.html at minimum.
    
    Args:
        preview_path: Path to preview directory
    
    Returns:
        True if structure is valid
    """
    dist_dir = preview_path / "dist"
    index_html = dist_dir / "index.html"
    
    if not dist_dir.exists():
        logger.warning(f"Missing dist/ directory in {preview_path}")
        return False
    
    if not index_html.exists():
        logger.warning(f"Missing index.html in {preview_path}/dist/")
        return False
    
    return True


def _remove_preview_dir(preview_path: Path) -> bool:
    """Safely remove preview directory."""
    try:
        if preview_path.exists() and preview_path.is_dir():
            shutil.rmtree(preview_path)
            return True
    except Exception as e:
        logger.error(f"Failed to remove {preview_path}: {e}")
    return False


def _get_dir_size_mb(path: Path) -> float:
    """Calculate directory size in MB."""
    try:
        total = 0
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error calculating size: {e}")
        return 0
