from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class JobPaths:
    root: Path
    input_video: Path
    audio_wav: Path
    subtitles_json: Path
    output_srt: Path


def get_default_storage_root() -> Path:
    return Path(__file__).resolve().parents[3] / "storage"


def build_job_paths(
    job_id: str,
    storage_root: Optional[Path] = None,
    input_extension: str = ".mp4",
) -> JobPaths:
    resolved_storage_root = storage_root or get_default_storage_root()
    normalized_extension = input_extension if input_extension.startswith(".") else f".{input_extension}"
    job_root = resolved_storage_root / "jobs" / job_id

    return JobPaths(
        root=job_root,
        input_video=job_root / f"input{normalized_extension}",
        audio_wav=job_root / "audio.wav",
        subtitles_json=job_root / "subtitles.json",
        output_srt=job_root / "output.srt",
    )
