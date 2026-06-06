import json
from typing import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.job_event import JobEvent, JobEventType
from app.services.job_event_service import JobEventService, job_event_service


def format_sse_event(event: JobEvent) -> str:
    return "event: {0}\ndata: {1}\n\n".format(
        event.type.value,
        json.dumps(event.model_dump(), ensure_ascii=False),
    )


def create_events_router(event_service: JobEventService = job_event_service) -> APIRouter:
    router = APIRouter()

    @router.get("/{job_id}/events")
    def stream_job_events(job_id: str) -> StreamingResponse:
        def event_stream() -> Iterator[str]:
            while True:
                event = event_service.next_event(job_id)
                if event is None:
                    yield ": keep-alive\n\n"
                    continue

                yield format_sse_event(event)
                if event.type == JobEventType.job_closed:
                    break

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    return router


router = create_events_router()
