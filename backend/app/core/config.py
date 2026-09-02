"""
RetailIQ — Application Configuration
Reads from environment variables / .env file
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "RetailIQ"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://retailiq:retailiq_pass@localhost:5432/retailiq"
    DATABASE_URL_SYNC: str = "postgresql://retailiq:retailiq_pass@localhost:5432/retailiq"
    SQLITE_URL: str = "sqlite:///./local_edge.db"

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # Simulation
    SIMULATION_MODE: bool = True
    SIMULATOR_TICK_SECONDS: float = 2.0
    SIMULATOR_STORE_ID: int = 1

    # Edge AI
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    YOLO_CONFIDENCE: float = 0.4
    FRAME_SKIP: int = 3
    FPS_LIMIT: int = 10
    CAMERA_SOURCE: str = "0"

    # WebSocket
    WS_HEARTBEAT_SECONDS: int = 30

    # Seed admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@retailiq.local"
    ADMIN_PASSWORD: str = "admin123"

    # Feature flags
    ENABLE_OFFLINE_MODE: bool = True
    ENABLE_EDGE_PIPELINE: bool = False
    ENABLE_REAL_YOLO: bool = False

    # Backend URL (used by simulator)
    BACKEND_URL: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
