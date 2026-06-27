from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel

from app.models.subtitle import SubtitleCue


class JobEventType(str, Enum):
    job_status = "job_status"
    subtitle_partial = "subtitle_partial"
    subtitle_translation_delta = "subtitle_translation_delta"
    job_done = "job_done"
    job_failed = "job_failed"
    job_closed = "job_closed"


class JobEvent(BaseModel):
    type: JobEventType
    job_id: str
    data: Dict[str, Any]

    @classmethod
    def status(
        cls,
        job_id: str,
        status: str,
        progress: int,
        message: str,
    ) -> "JobEvent":
        return cls(
            type=JobEventType.job_status,
            job_id=job_id,
            data={
                "status": status,
                "progress": progress,
                "message": message,
            },
        )

    @classmethod
    def subtitle_partial(cls, job_id: str, cue: SubtitleCue) -> "JobEvent":
        return cls(
            type=JobEventType.subtitle_partial,
            job_id=job_id,
            data={"cue": cue.model_dump()},
        )

    @classmethod
    def subtitle_translation_delta(
        cls,
        job_id: str,
        cue_index: int,
        delta: str,
        text: str,
    ) -> "JobEvent":
        return cls(
            type=JobEventType.subtitle_translation_delta,
            job_id=job_id,
            data={
                "cue_index": cue_index,
                "delta": delta,
                "text": text,
            },
        )

    @classmethod
    def done(cls, job_id: str) -> "JobEvent":
        return cls(type=JobEventType.job_done, job_id=job_id, data={})

    @classmethod
    def failed(cls, job_id: str, error: str) -> "JobEvent":
        return cls(
            type=JobEventType.job_failed,
            job_id=job_id,
            data={"error": error},
        )

    @classmethod
    def closed(cls, job_id: str) -> "JobEvent":
        return cls(type=JobEventType.job_closed, job_id=job_id, data={})
