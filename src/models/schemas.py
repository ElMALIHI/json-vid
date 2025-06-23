from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from .enums import (
    TransitionType,
    AudioEffect,
    VideoQuality,
    JobPriority,
    JobStatus
)

class AudioSettings(BaseModel):
    volume: float = Field(1.0, ge=0.0, le=2.0)
    effect: AudioEffect = AudioEffect.NONE
    start_time: float = Field(0.0, ge=0.0)
    end_time: Optional[float] = None
    loop: bool = False

class VideoSettings(BaseModel):
    quality: VideoQuality = VideoQuality.HIGH
    fps: int = Field(30, ge=15, le=60)
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[str] = None

class TextOverlay(BaseModel):
    text: str
    font: str = "DejaVu Sans"
    size: int = Field(32, ge=8, le=120)
    color: str = "#FFFFFF"
    position_x: float = Field(0.5, ge=0.0, le=1.0)
    position_y: float = Field(0.5, ge=0.0, le=1.0)
    start_time: float = 0.0
    end_time: Optional[float] = None

class Scene(BaseModel):
    media_path: str
    duration: float = Field(..., ge=0.1, le=60.0)
    transition: TransitionType = TransitionType.FADE
    transition_duration: float = Field(1.0, ge=0.1, le=5.0)
    audio: Optional[AudioSettings] = None
    text_overlays: List[TextOverlay] = []

class CompositionSettings(BaseModel):
    video_settings: VideoSettings = VideoSettings()
    background_audio: Optional[AudioSettings] = None
    watermark_path: Optional[str] = None
    watermark_opacity: float = Field(0.5, ge=0.0, le=1.0)

class VideoCompositionRequest(BaseModel):
    scenes: List[Scene] = Field(..., max_items=20)
    settings: CompositionSettings = CompositionSettings()
    priority: JobPriority = JobPriority.NORMAL
    webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = {}

    @validator('scenes')
    def validate_scenes(cls, v):
        total_duration = sum(scene.duration for scene in v)
        if total_duration > 600:  # 10 minutes
            raise ValueError("Total video duration cannot exceed 10 minutes")
        return v

class VideoJob(BaseModel):
    id: str
    request: VideoCompositionRequest
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    progress: float = 0.0

class JobsResponse(BaseModel):
    total: int
    jobs: List[VideoJob]
