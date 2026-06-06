from app.models.job_event import JobEvent, JobEventType
from app.models.subtitle import SubtitleCue


def test_job_event_serializes_status_payload():
    event = JobEvent.status(
        job_id="job_test",
        status="transcribing",
        progress=50,
        message="Transcribing speech.",
    )

    assert event.type == JobEventType.job_status
    assert event.job_id == "job_test"
    assert event.data == {
        "status": "transcribing",
        "progress": 50,
        "message": "Transcribing speech.",
    }


def test_job_event_serializes_subtitle_payload():
    cue = SubtitleCue(
        index=1,
        start=0.0,
        end=1.0,
        source_text="Hello",
        target_text="你好",
    )

    event = JobEvent.subtitle_partial(job_id="job_test", cue=cue)

    assert event.type == JobEventType.subtitle_partial
    assert event.data["cue"]["source_text"] == "Hello"
