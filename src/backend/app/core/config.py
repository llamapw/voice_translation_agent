import os
from dataclasses import dataclass, field
from typing import List, Optional


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "voice_translation_agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "0.1.0"))
    cors_origins: List[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:5173")
        )
    )
    default_source_language: str = field(
        default_factory=lambda: os.getenv("DEFAULT_SOURCE_LANGUAGE", "en")
    )
    default_target_language: str = field(
        default_factory=lambda: os.getenv("DEFAULT_TARGET_LANGUAGE", "zh")
    )
    ffmpeg_binary: str = field(default_factory=lambda: os.getenv("FFMPEG_BINARY", "ffmpeg"))
    asr_model: str = field(default_factory=lambda: os.getenv("ASR_MODEL", "fun-asr-realtime"))
    dashscope_websocket_url: str = field(
        default_factory=lambda: os.getenv(
            "DASHSCOPE_WEBSOCKET_URL",
            "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
        )
    )
    dashscope_api_key: Optional[str] = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY"))


settings = Settings()
