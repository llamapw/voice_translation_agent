import pytest

from app.models.job_event import JobEvent, JobEventType
from app.services.job_event_service import JobEventService


def test_job_event_service_publishes_event_to_subscriber():
    service = JobEventService()
    event = JobEvent.status(
        job_id="job_test",
        status="pending",
        progress=0,
        message="Waiting.",
    )

    service.publish(event)

    assert service.next_event("job_test", timeout=0.01) == event


def test_job_event_service_ignores_other_job_events():
    service = JobEventService()
    service.publish(
        JobEvent.status(
            job_id="job_other",
            status="done",
            progress=100,
            message="Done.",
        )
    )

    assert service.next_event("job_test", timeout=0.01) is None


def test_job_event_service_closes_job_stream():
    service = JobEventService()

    service.close("job_test")

    event = service.next_event("job_test", timeout=0.01)
    assert event is not None
    assert event.type == JobEventType.job_closed
