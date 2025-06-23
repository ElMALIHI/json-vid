from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "Enhanced Video Composition API"
    API_VERSION: str = "2.0.0"
    API_DESCRIPTION: str = "Advanced API for creating videos from images, audio, and video clips with transitions, effects, and overlays"
    API_KEY: str = os.getenv("API_KEY", "vK8mN2pQ7xR4sL9wE3tY6uI0oP5aS1dF8gH2jM4nB7cV9zX6qW3eR8tY5uI2oP0a")

    # File Limits
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_SCENES: int = 20
    MAX_DURATION_PER_SCENE: int = 60  # seconds
    MAX_TOTAL_DURATION: int = 600  # 10 minutes
    MAX_CONCURRENT_JOBS: int = 5

    # File Types
    ALLOWED_IMAGE_TYPES: set = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    ALLOWED_AUDIO_TYPES: set = {'.mp3', '.wav', '.m4a', '.aac', '.flac'}
    ALLOWED_VIDEO_TYPES: set = {'.mp4', '.avi', '.mov', '.mkv'}

    # Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    GENERATED_DIR: Path = BASE_DIR / "generated"
    TEMP_DIR: Path = BASE_DIR / "temp"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./video_jobs.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    class Config:
        case_sensitive = True

    def create_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.UPLOAD_DIR, self.GENERATED_DIR, self.TEMP_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.create_directories()
