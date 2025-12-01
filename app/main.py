"""
FastAPI server for serving files from DVC repository with version control support.
"""
import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
import dvc.api


# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get the git repository URL - REQUIRED
# Must be set to git repo URL (can be local git path or remote URL)
# Example: https://github.com/your-org/dvc-repo.git
# Or local: /path/to/dvc-repo (must be a git repo)
GIT_REPO_URL = os.getenv("GIT_REPO_URL")
if not GIT_REPO_URL:
    logger.error("GIT_REPO_URL environment variable is required")
    raise ValueError("GIT_REPO_URL environment variable must be set")

REPO_PATH = GIT_REPO_URL
logger.info(f"Using git repository: {REPO_PATH}")

app = FastAPI(
    title="DVC Repository API",
    description="API for accessing version-controlled files from DVC repository",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "DVC Repository API",
        "endpoints": {
            "known-non-issues": "/known-non-issues-el10/{package}",
            "generic": "/file?path={file_path}&rev={revision}",
            "check-exists": "/exists?path={file_path}&rev={revision}",
            "prompts": "/prompts/{filename}",
            "testing-data": "/testing-data-nvrs"
        }
    }


@app.get("/known-non-issues-el10/{package}")
async def get_known_non_issues(
    package: str,
    rev: Optional[str] = Query(None, description="Git revision/branch/tag (default: HEAD)")
):
    """
    Get ignore.err file for a specific package from known-non-issues-el10.
    
    Args:
        package: Package name (e.g., 'adcli', 'acl')
        rev: Optional git revision (branch, tag, or commit hash)
    
    Returns:
        The ignore.err file content
    """
    file_path = f"known-non-issues-el10/{package}/ignore.err"
    logger.info(f"Fetching {file_path} (rev={rev or 'HEAD'})")
    
    try:
        # Use DVC API to read the file with optional revision
        content = dvc.api.read(
            path=file_path,
            repo=str(REPO_PATH),
            rev=rev,
            mode='rb'
        )
        logger.info(f"Successfully fetched {file_path} ({len(content)} bytes)")
        
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=ignore.err",
                "X-Package": package,
                "X-Path": file_path
            }
        )
    
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404,
            detail=f"Package '{package}' not found or does not have ignore.err file"
        )
    except Exception as e:
        logger.error(f"Error retrieving file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving file: {str(e)}"
        )


@app.get("/prompts/{filename}")
async def get_prompt_file(
    filename: str,
    rev: Optional[str] = Query(None, description="Git revision/branch/tag (default: HEAD)")
):
    """
    Get a file from the prompts directory.
    
    Args:
        filename: File name in prompts directory (e.g., 'sast-ai-prompts.yaml')
        rev: Optional git revision (branch, tag, or commit hash)
    
    Returns:
        The requested file content
    """
    file_path = f"prompts/{filename}"
    logger.info(f"Fetching {file_path} (rev={rev or 'HEAD'})")
    
    try:
        content = dvc.api.read(
            path=file_path,
            repo=str(REPO_PATH),
            rev=rev,
            mode='rb'
        )
        logger.info(f"Successfully fetched {file_path} ({len(content)} bytes)")
        
        # Determine media type based on extension
        media_type = "application/octet-stream"
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            media_type = "application/x-yaml"
        elif filename.endswith('.json'):
            media_type = "application/json"
        elif filename.endswith('.txt'):
            media_type = "text/plain"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Path": file_path
            }
        )
    
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in prompts directory"
        )
    except Exception as e:
        logger.error(f"Error retrieving file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving file: {str(e)}"
        )


@app.get("/testing-data-nvrs")
async def get_testing_data_nvrs(
    rev: Optional[str] = Query(None, description="Git revision/branch/tag (default: HEAD)")
):
    """
    Get the testing-data-nvrs.yaml file.
    
    Args:
        rev: Optional git revision (branch, tag, or commit hash)
    
    Returns:
        The testing-data-nvrs.yaml file content
    """
    file_path = "testing-data-nvrs.yaml"
    logger.info(f"Fetching {file_path} (rev={rev or 'HEAD'})")
    
    try:
        content = dvc.api.read(
            path=file_path,
            repo=str(REPO_PATH),
            rev=rev,
            mode='rb'
        )
        logger.info(f"Successfully fetched {file_path} ({len(content)} bytes)")
        
        return Response(
            content=content,
            media_type="application/x-yaml",
            headers={
                "Content-Disposition": f"attachment; filename=testing-data-nvrs.yaml",
                "X-Path": file_path
            }
        )
    
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404,
            detail="testing-data-nvrs.yaml not found"
        )
    except Exception as e:
        logger.error(f"Error retrieving file {file_path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving file: {str(e)}"
        )


@app.get("/file")
async def get_file_by_path(
    path: str = Query(..., description="Relative path to the file in the repository"),
    rev: Optional[str] = Query(None, description="Git revision/branch/tag (default: HEAD)")
):
    """
    Generic endpoint to get any file from the repository by its full relative path.
    
    Args:
        path: Relative path to the file (e.g., 'known-non-issues-el10/adcli/ignore.err')
        rev: Optional git revision (branch, tag, or commit hash)
    
    Returns:
        The requested file content
    
    Examples:
        /file?path=known-non-issues-el10/adcli/ignore.err
        /file?path=prompts/sast-ai-prompts.yaml&rev=main
        /file?path=testing-data-nvrs.yaml&rev=v1.0.0
    """
    # Security: prevent path traversal attacks
    if ".." in path or path.startswith("/"):
        logger.warning(f"Path traversal attempt blocked: {path}")
        raise HTTPException(
            status_code=400,
            detail="Invalid path: path traversal not allowed"
        )
    
    logger.info(f"Fetching {path} (rev={rev or 'HEAD'})")
    
    try:
        # Use DVC API to read the file
        content = dvc.api.read(
            path=path,
            repo=str(REPO_PATH),
            rev=rev,
            mode='rb'
        )
        logger.info(f"Successfully fetched {path} ({len(content)} bytes)")
        
        # Extract filename for Content-Disposition header
        filename = Path(path).name
        
        # Determine media type based on extension
        media_type = "application/octet-stream"
        if path.endswith(('.yaml', '.yml')):
            media_type = "application/x-yaml"
        elif path.endswith('.json'):
            media_type = "application/json"
        elif path.endswith('.txt'):
            media_type = "text/plain"
        elif path.endswith(('.err', '.log')):
            media_type = "text/plain"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Path": path,
                "X-Revision": rev or "HEAD"
            }
        )
    
    except FileNotFoundError:
        logger.warning(f"File not found: {path}")
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {path}"
        )
    except Exception as e:
        logger.error(f"Error retrieving file {path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving file: {str(e)}"
        )


@app.get("/exists")
async def check_file_exists(
    path: str = Query(..., description="Relative path to the file in the repository"),
    rev: Optional[str] = Query(None, description="Git revision/branch/tag (default: HEAD)")
):
    """
    Check if a file exists in the repository without downloading it.
    
    Args:
        path: Relative path to the file (e.g., 'known-non-issues-el10/adcli/ignore.err')
        rev: Optional git revision (branch, tag, or commit hash)
    
    Returns:
        JSON with exists status and file info
    
    Examples:
        /exists?path=known-non-issues-el10/adcli/ignore.err
        /exists?path=prompts/sast-ai-prompts.yaml&rev=main
    """
    # Security: prevent path traversal attacks
    if ".." in path or path.startswith("/"):
        logger.warning(f"Path traversal attempt blocked: {path}")
        raise HTTPException(
            status_code=400,
            detail="Invalid path: path traversal not allowed"
        )
    
    logger.info(f"Checking existence of {path} (rev={rev or 'HEAD'})")
    
    try:
        # Use DVC filesystem to check file existence
        fs = dvc.api.DVCFileSystem(
            url=REPO_PATH,
            rev=rev
        )
        
        file_exists = fs.exists(path)
        
        if file_exists:
            try:
                info = fs.info(path)
                return {
                    "exists": True,
                    "path": path,
                    "revision": rev or "HEAD",
                    "size": info.get("size", None),
                    "type": info.get("type", "file")
                }
            except:
                # If info fails, at least we know it exists
                return {
                    "exists": True,
                    "path": path,
                    "revision": rev or "HEAD"
                }
        else:
            return {
                "exists": False,
                "path": path,
                "revision": rev or "HEAD"
            }
    
    except Exception as e:
        logger.error(f"Error checking file existence {path}: {str(e)}")
        return {
            "exists": False,
            "path": path,
            "revision": rev or "HEAD",
            "error": str(e)
        }




@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "repo_path": str(REPO_PATH)
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting DVC Repository API server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

