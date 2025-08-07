import os
import logging
from decouple import config
from typing import List

class Settings:
    # Server Configuration
    HOST: str = config("HOST", default="0.0.0.0")
    PORT: int = config("PORT", default=8000, cast=int)
    DEBUG: bool = config("DEBUG", default=False, cast=bool)
    
    # Redis Configuration
    REDIS_HOST: str = config("REDIS_HOST", default="localhost")
    REDIS_PORT: int = config("REDIS_PORT", default=6379, cast=int)
    REDIS_DB: int = config("REDIS_DB", default=0, cast=int)
    REDIS_PASSWORD: str = config("REDIS_PASSWORD", default="")
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = config(
        "ALLOWED_ORIGINS", 
        default="http://localhost:3000,http://localhost:8080", 
        cast=lambda v: [s.strip() for s in v.split(',')]
    )
    
    # Logging Configuration
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    LOG_FILE: str = config("LOG_FILE", default="logs/app.log")
    
    # Audio Processing Configuration
    MAX_FILE_SIZE: int = config("MAX_FILE_SIZE", default=100 * 1024 * 1024, cast=int)  # 100MB
    SUPPORTED_FORMATS: List[str] = config(
        "SUPPORTED_FORMATS",
        default="wav,mp3,flac,m4a,ogg",
        cast=lambda v: [s.strip() for s in v.split(',')]
    )
    
    # Feature Extraction Settings
    SAMPLE_RATE: int = config("SAMPLE_RATE", default=22050, cast=int)
    HOP_LENGTH: int = config("HOP_LENGTH", default=512, cast=int)
    N_MELS: int = config("N_MELS", default=128, cast=int)
    N_MFCC: int = config("N_MFCC", default=13, cast=int)
    
    # Demucs Configuration
    DEMUCS_MODEL: str = config("DEMUCS_MODEL", default="htdemucs")
    DEMUCS_DEVICE: str = config("DEMUCS_DEVICE", default="auto")  # auto, cpu, cuda, mps
    
    # File Storage
    TEMP_DIR: str = config("TEMP_DIR", default="/tmp/audio_processing")
    OUTPUT_DIR: str = config("OUTPUT_DIR", default="outputs")
    
    # Task Configuration
    TASK_TIME_LIMIT: int = config("TASK_TIME_LIMIT", default=1800, cast=int)  # 30 minutes
    TASK_SOFT_TIME_LIMIT: int = config("TASK_SOFT_TIME_LIMIT", default=1500, cast=int)  # 25 minutes
    
    def __post_init__(self):
        # Create necessary directories
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.LOG_FILE),
                logging.StreamHandler()
            ]
        )

settings = Settings()
settings.__post_init__()