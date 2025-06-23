import hashlib
import base64
import aiofiles
import httpx
import os
from typing import Set
from pathlib import Path
from ..core.config import settings

async def get_file_hash(file_path: str) -> str:
    """Generate SHA256 hash of a file."""
    BUF_SIZE = 65536
    sha256 = hashlib.sha256()
    
    async with aiofiles.open(file_path, 'rb') as f:
        while True:
            data = await f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    
    return sha256.hexdigest()

def validate_file_type(filename: str, allowed_types: Set[str]) -> bool:
    """Validate if the file extension is allowed."""
    return Path(filename).suffix.lower() in allowed_types

async def save_base64_media(base64_data: str, file_extension: str) -> str:
    """Save base64 encoded media to a file."""
    try:
        # Remove base64 header if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64 data
        file_data = base64.b64decode(base64_data)
        
        # Generate unique filename
        filename = f"{hashlib.md5(file_data).hexdigest()}{file_extension}"
        file_path = settings.UPLOAD_DIR / filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
        
        return str(file_path)
    except Exception as e:
        raise ValueError(f"Error saving base64 media: {str(e)}")

async def download_remote_file(url: str, max_size: int = settings.MAX_FILE_SIZE) -> str:
    """Download a file from a remote URL."""
    async with httpx.AsyncClient() as client:
        # First, make a HEAD request to check content length
        head_response = await client.head(url)
        content_length = int(head_response.headers.get('content-length', 0))
        
        if content_length > max_size:
            raise ValueError(f"File size ({content_length}) exceeds maximum allowed size ({max_size})")
        
        # Download the file
        response = await client.get(url)
        response.raise_for_status()
        
        # Generate unique filename
        file_extension = Path(url).suffix
        filename = f"{hashlib.md5(response.content).hexdigest()}{file_extension}"
        file_path = settings.UPLOAD_DIR / filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(response.content)
        
        return str(file_path)

def cleanup_temp_files(job_id: str):
    """Clean up temporary files associated with a job."""
    temp_dir = settings.TEMP_DIR / job_id
    if temp_dir.exists():
        for file in temp_dir.glob("*"):
            try:
                file.unlink()
            except Exception:
                pass
        try:
            temp_dir.rmdir()
        except Exception:
            pass
