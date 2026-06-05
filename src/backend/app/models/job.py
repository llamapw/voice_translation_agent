from enum import Enum
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    pending = "pending"
    extracting_audio = "extracting_audio"
    transcribing = "transcribing"
    correcting = "correcting"
    translating = "translating"
    generating_subtitle = "generating_subtitle"
    done = "done"
    failed = "failed"


SubtitleMode = Literal["source", "target", "bilingual"]


class JobCreateOptions(BaseModel):
    source_language: str = "en"
    target_language: str = "zh"
    correct: bool = True
    asr_model: str = "paraformer-v2"
    llm_model: str = "default"
    subtitle_mode: SubtitleMode = "bilingual"


class JobRead(BaseModel):
    id: str = Field(default_factory=lambda: "job_{0}".format(uuid4().hex[:12]))
    status: JobStatus = JobStatus.pending
    progress: int = 0
    message: str = "Task is waiting to start."
    source_language: str = "en"
    target_language: str = "zh"
    correct: bool = True
    asr_model: str = "paraformer-v2"
    llm_model: str = "default"
    subtitle_mode: SubtitleMode = "bilingual"
    original_filename: Optional[str] = None
    input_extension: str = ".mp4"
    video_url: Optional[str] = None
    subtitle_url: Optional[str] = None
    srt_download_url: Optional[str] = None
    error: Optional[str] = None
