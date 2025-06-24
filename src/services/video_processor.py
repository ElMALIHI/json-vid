import asyncio
import logging
from pathlib import Path
from typing import Optional
from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip
from PIL import Image
import cv2
import numpy as np
from ..models.schemas import VideoJob, Scene, VideoCompositionRequest
from ..models.enums import JobStatus, TransitionType
from ..core.config import settings
from ..utils.file_handlers import cleanup_temp_files

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.active_jobs = set()
        self._processing_lock = asyncio.Lock()

    async def process_job(self, job: VideoJob) -> None:
        """Process a video composition job."""
        if len(self.active_jobs) >= settings.MAX_CONCURRENT_JOBS:
            logger.warning(f"Maximum concurrent jobs limit reached. Job {job.id} queued.")
            return

        async with self._processing_lock:
            if job.id in self.active_jobs:
                return
            self.active_jobs.add(job.id)

        try:
            job.status = JobStatus.PROCESSING
            output_path = await self._create_composition(job.request)
            
            job.status = JobStatus.COMPLETED
            job.output_path = str(output_path)
            job.progress = 100.0
            
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {str(e)}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
        finally:
            self.active_jobs.remove(job.id)
            cleanup_temp_files(job.id)

    async def _create_composition(self, request: VideoCompositionRequest) -> Path:
        """Create the video composition from the request."""
        clips = []
        temp_dir = settings.TEMP_DIR / "processing"
        temp_dir.mkdir(parents=True, exist_ok=True)

        for i, scene in enumerate(request.scenes):
            clip = await self._process_scene(scene, temp_dir)
            if i > 0:
                clip = self._apply_transition(
                    clips[-1], 
                    clip, 
                    scene.transition, 
                    scene.transition_duration
                )
            clips.append(clip)

        # Combine all clips
        final_clip = CompositeVideoClip(clips)

        # Apply background audio if specified
        if request.settings.background_audio:
            audio = AudioFileClip(request.settings.background_audio.media_path)
            final_clip = final_clip.set_audio(audio)

        # Apply watermark if specified
        if request.settings.watermark_path:
            watermark = self._create_watermark(
                request.settings.watermark_path,
                request.settings.watermark_opacity,
                final_clip.size
            )
            final_clip = CompositeVideoClip([final_clip, watermark])

        # Generate output path
        output_path = settings.GENERATED_DIR / f"{hash(request)}.mp4"
        
        # Write the final video
        final_clip.write_videofile(
            str(output_path),
            fps=request.settings.video_settings.fps,
            codec='libx264',
            audio_codec='aac',
            bitrate=request.settings.video_settings.bitrate
        )

        return output_path

    async def _process_scene(self, scene: Scene, temp_dir: Path) -> VideoFileClip:
        """Process a single scene. Accepts local file paths or URLs."""
        import re
        from ..utils.file_handlers import download_remote_file

        media_path_str = scene.media_path
        # Check if media_path is a URL
        if re.match(r'^https?://', media_path_str):
            # Download the file and use the local path
            media_path_str = await download_remote_file(media_path_str)
        media_path = Path(media_path_str)
        
        if media_path.suffix.lower() in settings.ALLOWED_VIDEO_TYPES:
            clip = VideoFileClip(str(media_path))
        elif media_path.suffix.lower() in settings.ALLOWED_IMAGE_TYPES:
            clip = ImageClip(str(media_path), duration=scene.duration)
        else:
            raise ValueError(f"Unsupported media type: {media_path.suffix}")

        # Apply text overlays
        if scene.text_overlays:
            for overlay in scene.text_overlays:
                txt_clip = self._create_text_overlay(overlay, clip.size)
                clip = CompositeVideoClip([clip, txt_clip])

        # Apply audio settings
        if scene.audio:
            if scene.audio.effect != "none":
                clip = self._apply_audio_effect(clip, scene.audio)

        return clip

    def _apply_transition(
        self, 
        clip1: VideoFileClip, 
        clip2: VideoFileClip, 
        transition: TransitionType, 
        duration: float
    ) -> VideoFileClip:
        """Apply transition between two clips."""
        # Implementation of different transitions
        if transition == TransitionType.FADE:
            return self._crossfade_clips(clip1, clip2, duration)
        # Add more transition implementations here
        return clip2

    def _create_text_overlay(self, overlay, size) -> VideoFileClip:
        """Create a text overlay clip."""
        # Implementation of text overlay creation
        pass

    def _apply_audio_effect(self, clip: VideoFileClip, audio_settings) -> VideoFileClip:
        """Apply audio effects to a clip."""
        # Implementation of audio effects
        pass

    def _create_watermark(self, watermark_path: str, opacity: float, size) -> VideoFileClip:
        """Create a watermark overlay."""
        # Implementation of watermark creation
        pass

    def _crossfade_clips(
        self, 
        clip1: VideoFileClip, 
        clip2: VideoFileClip, 
        duration: float
    ) -> VideoFileClip:
        """Create a crossfade transition between two clips."""
        # Implementation of crossfade transition
        pass
