from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form, Depends, Security, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime
from pathlib import Path
import aiofiles

from ..core.config import settings
from ..models.schemas import (
    VideoCompositionRequest,
    VideoJob,
    JobsResponse
)
from ..models.enums import JobStatus
from ..services.video_processor import VideoProcessor
from ..utils.file_handlers import (
    validate_file_type,
    save_base64_media,
    download_remote_file
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize VideoProcessor
video_processor = VideoProcessor()

# Global storage for jobs (in a real application, this would be a database)
jobs_storage: Dict[str, VideoJob] = {}

async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Verify API key for protected endpoints."""
    if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health"]:
        return True
    
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return True

@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_file(file: UploadFile = File(...)):
    """Upload a single media file."""
    if not validate_file_type(file.filename, {
        *settings.ALLOWED_IMAGE_TYPES,
        *settings.ALLOWED_AUDIO_TYPES,
        *settings.ALLOWED_VIDEO_TYPES
    }):
        raise HTTPException(
            status_code=400,
            detail="File type not allowed"
        )

    file_path = settings.UPLOAD_DIR / f"{uuid.uuid4()}{Path(file.filename).suffix}"
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):
                await f.write(chunk)
        return {"file_path": str(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compose", response_model=Dict[str, str], dependencies=[Depends(verify_api_key)])
async def create_composition(
    request: VideoCompositionRequest,
    background_tasks: BackgroundTasks
):
    """Create a new video composition."""
    job_id = str(uuid.uuid4())
    job = VideoJob(
        id=job_id,
        request=request,
        status=JobStatus.PENDING
    )
    
    jobs_storage[job_id] = job
    background_tasks.add_task(video_processor.process_job, job)
    
    return {"job_id": job_id}

@app.get("/job/{job_id}", response_model=VideoJob, dependencies=[Depends(verify_api_key)])
async def get_job_status(job_id: str):
    """Get the status of a specific job."""
    if job_id not in jobs_storage:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    return jobs_storage[job_id]

@app.get("/jobs", response_model=JobsResponse, dependencies=[Depends(verify_api_key)])
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 10,
    offset: int = 0
):
    """List all jobs with optional filtering."""
    filtered_jobs = [
        job for job in jobs_storage.values()
        if status is None or job.status == status
    ]
    
    return JobsResponse(
        total=len(filtered_jobs),
        jobs=filtered_jobs[offset:offset + limit]
    )

@app.get("/download/{job_id}", dependencies=[Depends(verify_api_key)])
async def download_video(job_id: str):
    """Download the processed video."""
    if job_id not in jobs_storage:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job = jobs_storage[job_id]
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Output file not found"
        )
    
    return FileResponse(
        job.output_path,
        media_type="video/mp4",
        filename=f"video_{job_id}.mp4"
    )

@app.delete("/job/{job_id}", dependencies=[Depends(verify_api_key)])
async def delete_job(job_id: str):
    """Delete a job and its associated files."""
    if job_id not in jobs_storage:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job = jobs_storage[job_id]
    if job.output_path:
        try:
            Path(job.output_path).unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error deleting output file: {e}")
    
    del jobs_storage[job_id]
    return {"message": "Job deleted successfully"}
