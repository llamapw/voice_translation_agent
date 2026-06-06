from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI

from app.api.routes_events import create_events_router
from app.api.routes_insights import create_insights_router
from app.api.routes_jobs import create_jobs_router
from app.api.routes_subtitles import create_subtitles_router
from app.core.config import settings
from app.services.insight_service import ConfiguredInsightAgent, InsightService
from app.services.job_event_service import job_event_service
from app.services.job_service import job_service
from app.services.media_service import media_service
from app.services.subtitle_service import subtitle_service


def create_app(
    storage_root: Optional[Path] = None,
    use_real_worker: Optional[bool] = None,
    use_langchain_insight_agent: Optional[bool] = None,
) -> FastAPI:
    created_app = FastAPI(title="voice_translation_agent")
    resolved_use_real_worker = settings.use_real_worker if use_real_worker is None else use_real_worker
    resolved_use_langchain_insight_agent = (
        settings.use_langchain_insight_agent
        if use_langchain_insight_agent is None
        else use_langchain_insight_agent
    )
    created_app.include_router(
        create_jobs_router(
            job_service=job_service,
            media_service=media_service,
            subtitle_service=subtitle_service,
            storage_root=storage_root,
            use_real_worker=resolved_use_real_worker,
        ),
        prefix="/api/jobs",
    )
    created_app.include_router(
        create_subtitles_router(storage_root=storage_root),
        prefix="/api/jobs",
    )
    created_app.include_router(
        create_events_router(event_service=job_event_service),
        prefix="/api/jobs",
    )
    created_app.include_router(
        create_insights_router(
            insight_service=InsightService(
                agent=ConfiguredInsightAgent(
                    use_langchain=resolved_use_langchain_insight_agent,
                )
            ),
            storage_root=storage_root,
        ),
        prefix="/api/jobs",
    )

    @created_app.get("/health")
    def read_health() -> Dict[str, str]:
        return {
            "status": "ok",
            "service": "voice_translation_agent",
        }

    return created_app


app = create_app()
