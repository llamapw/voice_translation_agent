from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_events import create_events_router
from app.models.job_event import JobEvent
from app.services.job_event_service import JobEventService


def build_test_client(event_service):
    app = FastAPI()
    app.include_router(
        create_events_router(event_service=event_service),
        prefix="/api/jobs",
    )
    return TestClient(app)


def test_events_route_streams_published_job_event():
    event_service = JobEventService()
    event_service.publish(
        JobEvent.status(
            job_id="job_test",
            status="transcribing",
            progress=50,
            message="Transcribing speech.",
        )
    )
    event_service.close("job_test")
    client = build_test_client(event_service)

    response = client.get("/api/jobs/job_test/events")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: job_status" in response.text
    assert '"status": "transcribing"' in response.text
    assert "event: job_closed" in response.text
