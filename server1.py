from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import os
import uuid
import asyncio
import aiofiles
import base64
import hashlib
import json
import logging
import mimetypes
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Settings:
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_SCENES = 20
    MAX_DURATION_PER_SCENE = 60  # seconds
    MAX_TOTAL_DURATION = 600  # 10 minutes
    ALLOWED_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    ALLOWED_AUDIO_TYPES = {'.mp3', '.wav', '.m4a', '.aac', '.flac'}
    ALLOWED_VIDEO_TYPES = {'.mp4', '.avi', '.mov', '.mkv'}
    UPLOAD_DIR = "uploads"
    GENERATED_DIR = "generated"
    TEMP_DIR = "temp"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./video_jobs.db")
    API_KEY = os.getenv("API_KEY", "vK8mN2pQ7xR4sL9wE3tY6uI0oP5aS1dF8gH2jM4nB7cV9zX6qW3eR8tY5uI2oP0a")
    MAX_CONCURRENT_JOBS = 5

settings = Settings()

# Create directories
for directory in [settings.UPLOAD_DIR, settings.GENERATED_DIR, settings.TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Security
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

# Enhanced Enums
class TransitionType(str, Enum):
    FADE = "fade"
    CUT = "cut"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DISSOLVE = "dissolve"
    CROSSFADE = "crossfade"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"
    CIRCLE_OPEN = "circle_open"
    CIRCLE_CLOSE = "circle_close"

class AudioEffect(str, Enum):
    NONE = "none"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    NORMALIZE = "normalize"
    AMPLIFY = "amplify"
    NOISE_REDUCTION = "noise_reduction"

class VideoQuality(str, Enum):
    LOW = "480p"
    MEDIUM = "720p"
    HIGH = "1080p"
    ULTRA = "1440p"
    UHD = "2160p"

class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

# Enhanced Models
class AudioSettings(BaseModel):
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Audio volume multiplier")
    effects: List[AudioEffect] = Field(default=[AudioEffect.NONE], description="Audio effects to apply")
    start_time: Optional[float] = Field(None, ge=0, description="Audio start time in seconds")
    end_time: Optional[float] = Field(None, ge=0, description="Audio end time in seconds")

class VideoSettings(BaseModel):
    scale: Optional[str] = Field(None, description="Scale filter (e.g., '1920:1080')")
    crop: Optional[str] = Field(None, description="Crop filter (e.g., '1920:1080:0:0')")
    rotate: Optional[int] = Field(0, ge=0, le=360, description="Rotation angle in degrees")
    brightness: float = Field(1.0, ge=0.1, le=3.0, description="Brightness multiplier")
    contrast: float = Field(1.0, ge=0.1, le=3.0, description="Contrast multiplier")
    saturation: float = Field(1.0, ge=0.0, le=3.0, description="Saturation multiplier")

class TextOverlay(BaseModel):
    text: str = Field(..., description="Text to overlay")
    position: str = Field(default="center", description="Position (center, top, bottom, left, right)")
    font_size: int = Field(default=24, ge=8, le=200, description="Font size")
    font_color: str = Field(default="white", description="Font color (name or hex)")
    background_color: Optional[str] = Field(None, description="Background color for text")
    duration: Optional[float] = Field(None, ge=0, description="Text display duration")
    start_time: float = Field(default=0, ge=0, description="When to start showing text")

class Scene(BaseModel):
    source: str = Field(..., description="URL, file path, or base64 encoded media")
    media_type: str = Field(default="image", description="Media type: image, video, or audio")
    voiceover: Optional[str] = Field(None, description="Voiceover audio source")
    voiceover_base64: Optional[str] = Field(None, description="Base64 encoded audio data")
    background_music: Optional[str] = Field(None, description="Background music source")
    transition: TransitionType = Field(default=TransitionType.FADE)
    transition_duration: float = Field(default=0.5, ge=0, le=3.0, description="Transition duration in seconds")
    duration: Optional[float] = Field(None, ge=0.1, le=settings.MAX_DURATION_PER_SCENE)
    audio_settings: AudioSettings = Field(default_factory=AudioSettings)
    video_settings: VideoSettings = Field(default_factory=VideoSettings)
    text_overlays: List[TextOverlay] = Field(default=[], description="Text overlays for this scene")
    loop: bool = Field(default=False, description="Loop media if shorter than duration")
    
    @validator('source')
    def validate_source(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Source must be a non-empty string')
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        if v and v > settings.MAX_DURATION_PER_SCENE:
            raise ValueError(f'Duration cannot exceed {settings.MAX_DURATION_PER_SCENE} seconds')
        return v

class CompositionSettings(BaseModel):
    background_color: str = Field(default="black", description="Background color")
    background_music: Optional[str] = Field(None, description="Global background music")
    background_music_volume: float = Field(default=0.3, ge=0.0, le=1.0)
    intro_duration: float = Field(default=0, ge=0, le=10, description="Intro duration in seconds")
    outro_duration: float = Field(default=0, ge=0, le=10, description="Outro duration in seconds")
    crossfade_audio: bool = Field(default=True, description="Crossfade audio between scenes")

class VideoCompositionRequest(BaseModel):
    scenes: Dict[str, Scene] = Field(..., description="Dictionary of scenes")
    output_format: str = Field(default="mp4", description="Output format")
    quality: VideoQuality = Field(default=VideoQuality.HIGH)
    fps: int = Field(default=30, ge=15, le=60, description="Frames per second")
    priority: JobPriority = Field(default=JobPriority.NORMAL)
    composition_settings: CompositionSettings = Field(default_factory=CompositionSettings)
    webhook_url: Optional[str] = Field(None, description="Webhook URL for job completion notification")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    
    @validator('scenes')
    def validate_scenes(cls, v):
        if not v:
            raise ValueError('At least one scene is required')
        if len(v) > settings.MAX_SCENES:
            raise ValueError(f'Maximum {settings.MAX_SCENES} scenes allowed')
        
        total_duration = 0
        for key, scene in v.items():
            if not key.startswith('Scene '):
                raise ValueError(f'Scene key "{key}" must follow format "Scene X"')
            if scene.duration:
                total_duration += scene.duration
                
        if total_duration > settings.MAX_TOTAL_DURATION:
            raise ValueError(f'Total duration cannot exceed {settings.MAX_TOTAL_DURATION} seconds')
            
        return v

class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class VideoJob(BaseModel):
    job_id: str
    status: JobStatus
    priority: JobPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    output_url: Optional[str] = None
    preview_url: Optional[str] = None
    error_message: Optional[str] = None
    progress: int = Field(default=0, ge=0, le=100)
    estimated_time_remaining: Optional[int] = None  # seconds
    file_size: Optional[int] = None  # bytes
    duration: Optional[float] = None  # video duration in seconds
    metadata: Dict[str, Any] = Field(default={})

class JobsResponse(BaseModel):
    jobs: List[VideoJob]
    total: int
    page: int
    per_page: int
    total_pages: int

# Global state
jobs_storage: Dict[str, VideoJob] = {}
processing_jobs: set = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Video Composition API")
    yield
    # Shutdown
    logger.info("Shutting down Video Composition API")

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Video Composition API",
    version="2.0.0",
    description="Advanced API for creating videos from images, audio, and video clips with transitions, effects, and overlays",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions
def get_file_hash(file_path: str) -> str:
    """Generate MD5 hash of file for deduplication"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def validate_file_type(filename: str, allowed_types: set) -> bool:
    """Validate file type based on extension"""
    return Path(filename).suffix.lower() in allowed_types

async def save_base64_media(base64_data: str, file_extension: str) -> str:
    """Save base64 encoded media data to file"""
    try:
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',')[1]
        
        media_data = base64.b64decode(base64_data)
        
        if len(media_data) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(media_data)
        
        return file_path
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 data: {str(e)}")

async def download_remote_file(url: str, max_size: int = settings.MAX_FILE_SIZE) -> str:
    """Download file from URL and save locally"""
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', url) as response:
                response.raise_for_status()
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > max_size:
                    raise HTTPException(status_code=413, detail="Remote file too large")
                
                # Generate filename
                file_id = str(uuid.uuid4())
                content_type = response.headers.get('content-type', '')
                extension = mimetypes.guess_extension(content_type) or '.bin'
                filename = f"{file_id}{extension}"
                file_path = os.path.join(settings.TEMP_DIR, filename)
                
                # Download and save
                downloaded_size = 0
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        downloaded_size += len(chunk)
                        if downloaded_size > max_size:
                            await aiofiles.os.remove(file_path)
                            raise HTTPException(status_code=413, detail="Remote file too large")
                        await f.write(chunk)
                
                return file_path
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to download file: {str(e)}")

# Enhanced API endpoints
@app.get("/")
async def root():
    return {
        "message": "Enhanced Video Composition API",
        "version": "2.0.0",
        "features": [
            "Advanced transitions and effects",
            "Text overlays",
            "Audio mixing",
            "Video processing",
            "Background music",
            "Job prioritization",
            "Webhook notifications",
            "File deduplication"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len(processing_jobs),
        "total_jobs": len(jobs_storage)
    }

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Upload media files with enhanced validation and deduplication"""
    
    # Validate file type
    all_allowed_types = (
        settings.ALLOWED_IMAGE_TYPES | 
        settings.ALLOWED_AUDIO_TYPES | 
        settings.ALLOWED_VIDEO_TYPES
    )
    
    if not validate_file_type(file.filename, all_allowed_types):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Supported: {', '.join(all_allowed_types)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Generate file info
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{file_id}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Generate file hash for deduplication
    file_hash = get_file_hash(file_path)
    
    # Determine media type
    media_type = "unknown"
    if file_extension.lower() in settings.ALLOWED_IMAGE_TYPES:
        media_type = "image"
    elif file_extension.lower() in settings.ALLOWED_AUDIO_TYPES:
        media_type = "audio"
    elif file_extension.lower() in settings.ALLOWED_VIDEO_TYPES:
        media_type = "video"
    
    return {
        "file_id": file_id,
        "filename": filename,
        "original_name": file.filename,
        "file_path": file_path,
        "file_hash": file_hash,
        "media_type": media_type,
        "file_size": len(content),
        "use_in_request": f"uploads/{filename}"
    }

@app.post("/upload-batch")
async def upload_batch_files(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Upload multiple files at once"""
    uploaded_files = []
    
    for file in files:
        try:
            # Validate file type
            all_allowed_types = (
                settings.ALLOWED_IMAGE_TYPES | 
                settings.ALLOWED_AUDIO_TYPES | 
                settings.ALLOWED_VIDEO_TYPES
            )
            
            if not validate_file_type(file.filename, all_allowed_types):
                uploaded_files.append({
                    "original_name": file.filename,
                    "status": "failed",
                    "error": "File type not allowed"
                })
                continue
            
            content = await file.read()
            if len(content) > settings.MAX_FILE_SIZE:
                uploaded_files.append({
                    "original_name": file.filename,
                    "status": "failed",
                    "error": "File too large"
                })
                continue
            
            # Save file
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            filename = f"{file_id}{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            file_hash = get_file_hash(file_path)
            
            # Determine media type
            media_type = "unknown"
            if file_extension.lower() in settings.ALLOWED_IMAGE_TYPES:
                media_type = "image"
            elif file_extension.lower() in settings.ALLOWED_AUDIO_TYPES:
                media_type = "audio"
            elif file_extension.lower() in settings.ALLOWED_VIDEO_TYPES:
                media_type = "video"
            
            uploaded_files.append({
                "file_id": file_id,
                "filename": filename,
                "original_name": file.filename,
                "use_in_request": f"uploads/{filename}",
                "media_type": media_type,
                "file_hash": file_hash,
                "file_size": len(content),
                "status": "success"
            })
            
        except Exception as e:
            uploaded_files.append({
                "original_name": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {"uploaded_files": uploaded_files}

@app.post("/compose", response_model=Dict[str, str])
async def create_video_composition(
    request: VideoCompositionRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Create enhanced video composition job with advanced features"""
    
    # Check if too many jobs are processing
    if len(processing_jobs) >= settings.MAX_CONCURRENT_JOBS:
        raise HTTPException(
            status_code=429, 
            detail=f"Too many concurrent jobs. Max: {settings.MAX_CONCURRENT_JOBS}"
        )
    
    job_id = str(uuid.uuid4())
    
    # Calculate expiration (24 hours from now)
    expires_at = datetime.now() + timedelta(hours=24)
    
    # Create enhanced job entry
    job = VideoJob(
        job_id=job_id,
        status=JobStatus.PENDING,
        priority=request.priority,
        created_at=datetime.now(),
        expires_at=expires_at,
        metadata=request.metadata
    )
    jobs_storage[job_id] = job
    
    # Add to processing queue
    background_tasks.add_task(process_enhanced_video_composition, job_id, request)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "priority": request.priority.value,
        "estimated_processing_time": "5-15 minutes",
        "expires_at": expires_at.isoformat(),
        "scenes_count": str(len(request.scenes)),
        "webhook_url": request.webhook_url if request.webhook_url else ""
    }

@app.get("/job/{job_id}", response_model=VideoJob)
async def get_job_status(job_id: str):
    """Get detailed job status with enhanced information"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    # Check if job has expired
    if job.expires_at and datetime.now() > job.expires_at and job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
        job.status = JobStatus.EXPIRED
    
    return job

@app.get("/jobs", response_model=JobsResponse)
async def list_jobs(
    page: int = 1,
    per_page: int = 10,
    status: Optional[JobStatus] = None,
    priority: Optional[JobPriority] = None
):
    """List jobs with pagination and filtering"""
    
    # Filter jobs
    filtered_jobs = list(jobs_storage.values())
    
    if status:
        filtered_jobs = [job for job in filtered_jobs if job.status == status]
    
    if priority:
        filtered_jobs = [job for job in filtered_jobs if job.priority == priority]
    
    # Sort by creation time (newest first)
    filtered_jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    # Pagination
    total = len(filtered_jobs)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_jobs = filtered_jobs[start_idx:end_idx]
    
    return JobsResponse(
        jobs=paginated_jobs,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@app.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download the generated video file"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job.output_url:
        raise HTTPException(status_code=404, detail="Output file not found")
    
    file_path = job.output_url.lstrip('/')
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=f"video_{job_id}.mp4",
        media_type="video/mp4"
    )

@app.delete("/job/{job_id}")
async def delete_job(job_id: str, api_key: str = Depends(verify_api_key)):
    """Delete a job and its associated files"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    # Cancel if processing
    if job.status == JobStatus.PROCESSING:
        job.status = JobStatus.CANCELLED
        processing_jobs.discard(job_id)
    
    # Delete output files
    if job.output_url and os.path.exists(job.output_url.lstrip('/')):
        os.remove(job.output_url.lstrip('/'))
    
    if job.preview_url and os.path.exists(job.preview_url.lstrip('/')):
        os.remove(job.preview_url.lstrip('/'))
    
    # Remove from storage
    del jobs_storage[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}

async def process_enhanced_video_composition(job_id: str, request: VideoCompositionRequest):
    """Enhanced background task for video composition with advanced features"""
    from moviepy.editor import (
        ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips, 
        concatenate_audioclips, CompositeVideoClip, TextClip, ColorClip
    )
    import requests
    from io import BytesIO
    from PIL import Image
    import numpy as np
    
    try:
        job = jobs_storage[job_id]
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now()
        processing_jobs.add(job_id)
        
        logger.info(f"Starting enhanced processing for job {job_id}")
        
        clips = []
        audio_clips = []
        total_scenes = len(request.scenes)
        
        # Process each scene with enhanced features
        for i, (scene_name, scene_data) in enumerate(request.scenes.items(), 1):
            logger.info(f"Processing {scene_name}")
            
            # Load media based on type
            if scene_data.source.startswith('http'):
                # Download remote file
                temp_path = await download_remote_file(scene_data.source)
                media_path = temp_path
            elif scene_data.source.startswith('data:'):
                # Handle base64 data
                media_type = scene_data.media_type or "image"
                ext = ".jpg" if media_type == "image" else ".mp4"
                media_path = await save_base64_media(scene_data.source, ext)
            else:
                media_path = scene_data.source
            
            # Create video clip based on media type
            if scene_data.media_type == "video":
                base_clip = VideoFileClip(media_path)
            else:
                # Image or audio treated as image with default duration
                if scene_data.media_type == "image" or not scene_data.media_type:
                    img = Image.open(media_path)
                    img_array = np.array(img)
                    duration = scene_data.duration or 5.0
                    base_clip = ImageClip(img_array).set_duration(duration)
                else:
                    # Audio-only scene - create black video
                    duration = scene_data.duration or 5.0
                    base_clip = ColorClip(
                        size=(1920, 1080), 
                        color=(0, 0, 0), 
                        duration=duration
                    )
            
            # Apply video settings
            if scene_data.video_settings.rotate:
                base_clip = base_clip.rotate(scene_data.video_settings.rotate)
            
            if scene_data.video_settings.brightness != 1.0:
                base_clip = base_clip.fx('multiply_brightness', scene_data.video_settings.brightness)
            
            # Add voiceover
            if scene_data.voiceover or scene_data.voiceover_base64:
                voiceover_path = None
                if scene_data.voiceover_base64:
                    voiceover_path = await save_base64_media(scene_data.voiceover_base64, ".mp3")
                elif scene_data.voiceover:
                    if scene_data.voiceover.startswith('http'):
                        voiceover_path = await download_remote_file(scene_data.voiceover)
                    else:
                        voiceover_path = scene_data.voiceover
                
                if voiceover_path:
                    audio_clip = AudioFileClip(voiceover_path)
                    
                    # Apply audio settings
                    if scene_data.audio_settings.volume != 1.0:
                        audio_clip = audio_clip.volumex(scene_data.audio_settings.volume)
                    
                    # Adjust video duration to match audio
                    if audio_clip.duration > base_clip.duration:
                        base_clip = base_clip.set_duration(audio_clip.duration)
                    
                    base_clip = base_clip.set_audio(audio_clip)
            
            # Add text overlays
            if scene_data.text_overlays:
                overlay_clips = [base_clip]
                
                for text_overlay in scene_data.text_overlays:
                    text_clip = TextClip(
                        text_overlay.text,
                        fontsize=text_overlay.font_size,
                        color=text_overlay.font_color,
                        bg_color=text_overlay.background_color
                    ).set_duration(text_overlay.duration or base_clip.duration)
                    
                    # Position text
                    if text_overlay.position == "center":
                        text_clip = text_clip.set_position('center')
                    elif text_overlay.position == "top":
                        text_clip = text_clip.set_position(('center', 'top'))
                    elif text_overlay.position == "bottom":
                        text_clip = text_clip.set_position(('center', 'bottom'))
                    
                    text_clip = text_clip.set_start(text_overlay.start_time)
                    overlay_clips.append(text_clip)
                
                if len(overlay_clips) > 1:
                    base_clip = CompositeVideoClip(overlay_clips)
            
            # Apply enhanced transitions
            if scene_data.transition != TransitionType.CUT and i > 1:
                transition_duration = scene_data.transition_duration
                
                if scene_data.transition == TransitionType.FADE:
                    base_clip = base_clip.fadein(transition_duration).fadeout(transition_duration)
                elif scene_data.transition == TransitionType.CROSSFADE:
                    base_clip = base_clip.crossfadein(transition_duration)
                elif scene_data.transition in [TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT]:
                    # Implement slide transitions using position animation
                    w, h = base_clip.size
                    if scene_data.transition == TransitionType.SLIDE_LEFT:
                        base_clip = base_clip.set_position(lambda t: (w * (1 - t/transition_duration) if t < transition_duration else 0, 0))
                    else:
                        base_clip = base_clip.set_position(lambda t: (-w * (1 - t/transition_duration) if t < transition_duration else 0, 0))
            
            clips.append(base_clip)
            
            # Update progress
            progress = int((i / total_scenes) * 80)  # Reserve 20% for final processing
            job.progress = progress
            
            logger.info(f"Completed processing {scene_name} ({i}/{total_scenes})")
        
        # Add background music if specified
        final_audio_clips = []
        if request.composition_settings.background_music:
            bg_music_path = request.composition_settings.background_music
            if bg_music_path.startswith('http'):
                bg_music_path = await download_remote_file(bg_music_path)
            
            bg_music = AudioFileClip(bg_music_path)
            bg_music = bg_music.volumex(request.composition_settings.background_music_volume)
            final_audio_clips.append(bg_music)
        
        # Combine all video clips
        logger.info("Combining video clips...")
        if request.composition_settings.crossfade_audio:
            final_video = concatenate_videoclips(clips, method="compose", padding=-0.5)
        else:
            final_video = concatenate_videoclips(clips, method="compose")
        
        # Add intro/outro if specified
        if request.composition_settings.intro_duration > 0:
            intro_clip = ColorClip(
                size=final_video.size,
                color=(0, 0, 0),
                duration=request.composition_settings.intro_duration
            )
            intro_text = TextClip(
                "Video Starting...",
                fontsize=50,
                color='white'
            ).set_duration(request.composition_settings.intro_duration).set_position('center')
            intro_composite = CompositeVideoClip([intro_clip, intro_text])
            final_video = concatenate_videoclips([intro_composite, final_video])
        
        if request.composition_settings.outro_duration > 0:
            outro_clip = ColorClip(
                size=final_video.size,
                color=(0, 0, 0),
                duration=request.composition_settings.outro_duration
            )
            outro_text = TextClip(
                "Thank You for Watching",
                fontsize=50,
                color='white'
            ).set_duration(request.composition_settings.outro_duration).set_position('center')
            outro_composite = CompositeVideoClip([outro_clip, outro_text])
            final_video = concatenate_videoclips([final_video, outro_composite])
        
        # Set final audio if background music exists
        if final_audio_clips:
            if final_video.audio:
                # Mix background music with existing audio
                mixed_audio = concatenate_audioclips([final_video.audio] + final_audio_clips)
                final_video = final_video.set_audio(mixed_audio)
            else:
                final_video = final_video.set_audio(final_audio_clips[0])
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{job_id}_{timestamp}.{request.output_format}"
        output_path = os.path.join(settings.GENERATED_DIR, output_filename)
        
        # Generate preview (first 10 seconds at lower quality)
        preview_filename = f"{job_id}_preview.mp4"
        preview_path = os.path.join(settings.GENERATED_DIR, preview_filename)
        
        logger.info("Generating preview...")
        preview_clip = final_video.subclip(0, min(10, final_video.duration))
        preview_clip.write_videofile(
            preview_path,
            fps=15,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            verbose=False,
            logger=None
        )
        
        job.progress = 90
        
        # Determine output quality settings
        quality_settings = {
            VideoQuality.LOW: {"preset": "fast", "crf": 28},
            VideoQuality.MEDIUM: {"preset": "medium", "crf": 23},
            VideoQuality.HIGH: {"preset": "slow", "crf": 18},
            VideoQuality.ULTRA: {"preset": "slower", "crf": 15},
            VideoQuality.UHD: {"preset": "veryslow", "crf": 12}
        }
        
        settings_for_quality = quality_settings.get(request.quality, quality_settings[VideoQuality.HIGH])
        
        logger.info(f"Rendering final video at {request.quality.value} quality...")
        
        # Write the final video with enhanced settings
        final_video.write_videofile(
            output_path,
            fps=request.fps,
            codec='libx264',
            audio_codec='aac',
            preset=settings_for_quality["preset"],
            ffmpeg_params=["-crf", str(settings_for_quality["crf"])],
            verbose=False,
            logger=None
        )
        
        # Get file size and duration
        file_size = os.path.getsize(output_path)
        video_duration = final_video.duration
        
        # Clean up temporary files
        final_video.close()
        for clip in clips:
            if hasattr(clip, 'close'):
                clip.close()
        
        # Mark as completed
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        job.progress = 100
        job.output_url = f"{settings.GENERATED_DIR}/{output_filename}"
        job.preview_url = f"{settings.GENERATED_DIR}/{preview_filename}"
        job.file_size = file_size
        job.duration = video_duration
        
        processing_jobs.discard(job_id)
        
        logger.info(f"Job {job_id} completed successfully")
        logger.info(f"Output: {output_path} ({file_size / (1024*1024):.1f} MB, {video_duration:.1f}s)")
        
        # Send webhook notification if provided
        if request.webhook_url:
            await send_webhook_notification(request.webhook_url, job)
        
    except Exception as e:
        # Handle errors
        job = jobs_storage.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            processing_jobs.discard(job_id)
        
        logger.error(f"Job {job_id} failed: {str(e)}")
        
        # Send webhook notification for failure
        if request.webhook_url and job:
            await send_webhook_notification(request.webhook_url, job)

async def send_webhook_notification(webhook_url: str, job: VideoJob):
    """Send webhook notification for job completion"""
    try:
        payload = {
            "job_id": job.job_id,
            "status": job.status.value,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "output_url": job.output_url,
            "preview_url": job.preview_url,
            "error_message": job.error_message,
            "file_size": job.file_size,
            "duration": job.duration,
            "metadata": job.metadata
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Webhook notification sent for job {job.job_id}")
            
    except Exception as e:
        logger.error(f"Failed to send webhook for job {job.job_id}: {e}")

@app.post("/cancel/{job_id}")
async def cancel_job(job_id: str, api_key: str = Depends(verify_api_key)):
    """Cancel a processing job"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    if job.status not in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now()
    processing_jobs.discard(job_id)
    
    return {"message": f"Job {job_id} cancelled successfully"}

@app.get("/queue-status")
async def get_queue_status():
    """Get current processing queue status"""
    pending_jobs = [job for job in jobs_storage.values() if job.status == JobStatus.PENDING]
    processing_jobs_list = [job for job in jobs_storage.values() if job.status == JobStatus.PROCESSING]
    
    return {
        "queue_length": len(pending_jobs),
        "processing_count": len(processing_jobs_list),
        "max_concurrent": settings.MAX_CONCURRENT_JOBS,
        "average_processing_time": "5-15 minutes",
        "pending_jobs": [
            {
                "job_id": job.job_id,
                "priority": job.priority.value,
                "created_at": job.created_at.isoformat(),
                "scenes_count": len(job.metadata.get("scenes", {}))
            } for job in sorted(pending_jobs, key=lambda x: (x.priority.value, x.created_at))
        ]
    }

@app.get("/statistics")
async def get_statistics():
    """Get API usage statistics"""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    jobs_today = [job for job in jobs_storage.values() if job.created_at >= today]
    completed_jobs = [job for job in jobs_storage.values() if job.status == JobStatus.COMPLETED]
    failed_jobs = [job for job in jobs_storage.values() if job.status == JobStatus.FAILED]
    
    total_processing_time = sum(
        (job.completed_at - job.started_at).total_seconds() 
        for job in completed_jobs 
        if job.started_at and job.completed_at
    )
    
    total_video_duration = sum(job.duration or 0 for job in completed_jobs)
    total_file_size = sum(job.file_size or 0 for job in completed_jobs)
    
    return {
        "total_jobs": len(jobs_storage),
        "jobs_today": len(jobs_today),
        "completed_jobs": len(completed_jobs),
        "failed_jobs": len(failed_jobs),
        "success_rate": len(completed_jobs) / len(jobs_storage) * 100 if jobs_storage else 0,
        "average_processing_time_seconds": total_processing_time / len(completed_jobs) if completed_jobs else 0,
        "total_video_duration_seconds": total_video_duration,
        "total_output_size_bytes": total_file_size,
        "current_processing": len(processing_jobs)
    }

@app.get("/templates")
async def get_composition_templates():
    """Get predefined composition templates"""
    return {
        "slideshow": {
            "description": "Simple slideshow with fade transitions",
            "composition_settings": {
                "background_color": "black",
                "crossfade_audio": True
            },
            "default_scene_settings": {
                "duration": 3.0,
                "transition": "fade",
                "transition_duration": 0.5
            }
        },
        "presentation": {
            "description": "Professional presentation style",
            "composition_settings": {
                "background_color": "white",
                "intro_duration": 2.0,
                "outro_duration": 2.0
            },
            "default_scene_settings": {
                "duration": 5.0,
                "transition": "slide_left",
                "transition_duration": 0.8,
                "text_overlays": [
                    {
                        "position": "bottom",
                        "font_size": 32,
                        "font_color": "black",
                        "background_color": "rgba(255,255,255,0.8)"
                    }
                ]
            }
        },
        "social_media": {
            "description": "Quick social media video",
            "quality": "medium",
            "composition_settings": {
                "background_music_volume": 0.4,
                "crossfade_audio": True
            },
            "default_scene_settings": {
                "duration": 2.0,
                "transition": "zoom_in",
                "transition_duration": 0.3
            }
        }
    }

@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported input and output formats"""
    return {
        "input_formats": {
            "images": list(settings.ALLOWED_IMAGE_TYPES),
            "audio": list(settings.ALLOWED_AUDIO_TYPES),
            "video": list(settings.ALLOWED_VIDEO_TYPES)
        },
        "output_formats": ["mp4", "avi", "mov", "webm"],
        "quality_levels": [q.value for q in VideoQuality],
        "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
        "max_scenes": settings.MAX_SCENES,
        "max_duration_per_scene": settings.MAX_DURATION_PER_SCENE,
        "max_total_duration": settings.MAX_TOTAL_DURATION
    }

@app.get("/example-requests")
async def get_example_requests():
    """Get comprehensive example requests"""
    return {
        "basic_slideshow": {
            "scenes": {
                "Scene 1": {
                    "source": "https://example.com/image1.jpg",
                    "duration": 3.0,
                    "transition": "fade"
                },
                "Scene 2": {
                    "source": "uploads/image2.jpg",
                    "voiceover": "uploads/narration.mp3",
                    "duration": 5.0,
                    "transition": "slide_left"
                }
            },
            "quality": "high",
            "fps": 30
        },
        "advanced_composition": {
            "scenes": {
                "Scene 1": {
                    "source": "uploads/intro_video.mp4",
                    "media_type": "video",
                    "voiceover": "uploads/intro_narration.mp3",
                    "background_music": "uploads/bg_music.mp3",
                    "transition": "fade",
                    "transition_duration": 1.0,
                    "audio_settings": {
                        "volume": 0.8,
                        "effects": ["normalize"]
                    },
                    "video_settings": {
                        "brightness": 1.1,
                        "contrast": 1.05
                    },
                    "text_overlays": [
                        {
                            "text": "Welcome to Our Presentation",
                            "position": "center",
                            "font_size": 48,
                            "font_color": "white",
                            "background_color": "rgba(0,0,0,0.5)",
                            "start_time": 1.0,
                            "duration": 3.0
                        }
                    ]
                }
            },
            "quality": "ultra",
            "fps": 60,
            "priority": "high",
            "composition_settings": {
                "background_color": "black",
                "background_music": "uploads/global_bg.mp3",
                "background_music_volume": 0.3,
                "intro_duration": 2.0,
                "outro_duration": 3.0,
                "crossfade_audio": True
            },
            "webhook_url": "https://your-app.com/webhook/video-complete",
            "metadata": {
                "project_name": "Marketing Video",
                "client": "Acme Corp",
                "version": "1.0"
            }
        }
    }

# Development and testing endpoints
@app.post("/test-webhook")
async def test_webhook(webhook_url: str):
    """Test webhook endpoint connectivity"""
    try:
        test_payload = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Webhook test successful"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=test_payload, timeout=10)
            response.raise_for_status()
            
        return {
            "success": True,
            "status_code": response.status_code,
            "response_time_ms": response.elapsed.total_seconds() * 1000
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )