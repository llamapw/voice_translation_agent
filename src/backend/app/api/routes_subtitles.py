import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.paths import build_job_paths, get_default_storage_root
from app.models.subtitle import SubtitleCue


def create_subtitles_router(storage_root: Optional[Path] = None) -> APIRouter:
    router = APIRouter()
    resolved_storage_root = storage_root or get_default_storage_root()

    @router.get("/{job_id}/subtitles", response_model=List[SubtitleCue])
    def read_subtitles(job_id: str) -> List[SubtitleCue]:
        path = build_job_paths(job_id, storage_root=resolved_storage_root).subtitles_json
        if not path.exists():
            raise HTTPException(status_code=404, detail="Subtitles not found.")

        payload = json.loads(path.read_text(encoding="utf-8"))
        return [SubtitleCue(**item) for item in payload]

    @router.get("/{job_id}/srt")
    def download_srt(job_id: str) -> FileResponse:
        path = build_job_paths(job_id, storage_root=resolved_storage_root).output_srt
        if not path.exists():
            raise HTTPException(status_code=404, detail="SRT not found.")

        return FileResponse(
            path=path,
            filename="{0}.srt".format(job_id),
            media_type="application/x-subrip",
        )

    return router


router = create_subtitles_router()
