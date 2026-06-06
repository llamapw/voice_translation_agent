import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _read_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def get_default_env_file() -> Path:
    return get_project_root() / ".env"


def load_env_file(path: Optional[Path]) -> Dict[str, str]:
    if path is None or not path.exists():
        return {}

    values: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


@dataclass
class Settings:
    app_name: str
    app_version: str
    cors_origins: List[str]
    default_source_language: str
    default_target_language: str
    ffmpeg_binary: str
    asr_model: str
    dashscope_websocket_url: str
    dashscope_api_key: Optional[str]
    llm_model: str
    llm_base_url: str
    llm_api_key: Optional[str]
    use_real_worker: bool

    def __init__(self, env_file: Optional[Path] = get_default_env_file()) -> None:
        env_values = load_env_file(env_file)

        def read(name: str, default: Optional[str] = None) -> Optional[str]:
            return os.getenv(name) or env_values.get(name) or default

        self.app_name = read("APP_NAME", "voice_translation_agent") or "voice_translation_agent"
        self.app_version = read("APP_VERSION", "0.1.0") or "0.1.0"
        self.cors_origins = _split_csv(read("CORS_ORIGINS", "http://localhost:5173") or "")
        self.default_source_language = read("DEFAULT_SOURCE_LANGUAGE", "en") or "en"
        self.default_target_language = read("DEFAULT_TARGET_LANGUAGE", "zh") or "zh"
        self.ffmpeg_binary = read("FFMPEG_BINARY", "ffmpeg") or "ffmpeg"
        self.asr_model = read("ASR_MODEL", "fun-asr-realtime") or "fun-asr-realtime"
        self.dashscope_websocket_url = (
            read(
                "DASHSCOPE_WEBSOCKET_URL",
                "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
            )
            or "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
        )
        self.dashscope_api_key = read("DASHSCOPE_API_KEY")
        self.llm_model = read("LLM_MODEL", "qwen-turbo") or "qwen-turbo"
        self.llm_base_url = read("LLM_BASE_URL", "https://api.qnaigc.com/v1") or "https://api.qnaigc.com/v1"
        self.llm_api_key = (
            read("LLM_API_KEY")
            or read("QINIU_AI_API_KEY")
            or read("qiniu_ai_api_key")
        )
        self.use_real_worker = _read_bool(read("USE_REAL_WORKER"), default=False)


settings = Settings()
