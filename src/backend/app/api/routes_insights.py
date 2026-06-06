from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.paths import build_job_paths, get_default_storage_root
from app.models.insight import InsightRead
from app.services.insight_service import (
    InsightNotFoundError,
    InsightService,
    InsightSourceNotFoundError,
    insight_service,
)


def create_insights_router(
    insight_service: InsightService = insight_service,
    storage_root: Optional[Path] = None,
) -> APIRouter:
    router = APIRouter()
    resolved_storage_root = storage_root or get_default_storage_root()

    @router.post("/{job_id}/insights", response_model=InsightRead)
    def generate_insight(job_id: str) -> InsightRead:
        try:
            return insight_service.generate_basic_insight(
                job_id,
                storage_root=resolved_storage_root,
            )
        except InsightSourceNotFoundError:
            raise HTTPException(status_code=404, detail="Subtitles not found.")

    @router.get("/{job_id}/insights", response_model=InsightRead)
    def read_insight(job_id: str) -> InsightRead:
        try:
            return insight_service.read_insight(
                job_id,
                storage_root=resolved_storage_root,
            )
        except InsightNotFoundError:
            raise HTTPException(status_code=404, detail="Insight not found.")

    @router.get("/{job_id}/insights/markdown")
    def download_insight_markdown(job_id: str) -> FileResponse:
        path = build_job_paths(job_id, storage_root=resolved_storage_root).insight_markdown
        if not path.exists():
            raise HTTPException(status_code=404, detail="Insight Markdown not found.")

        return FileResponse(
            path=path,
            filename="{0}-insight.md".format(job_id),
            media_type="text/markdown",
        )

    return router


router = create_insights_router()
