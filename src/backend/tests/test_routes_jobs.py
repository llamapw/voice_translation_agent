from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_jobs import create_jobs_router
from app.core.paths import build_job_paths
from app.models.job import JobStatus
from app.models.job_event import JobEventType
from app.services.job_event_service import JobEventService
from app.services.media_service import MediaService
from app.services.job_service import JobService
from app.services.subtitle_service import SubtitleService


def build_test_client(
    storage_root=None,
    use_real_worker=False,
    real_worker=None,
    event_service=None,
) -> TestClient:
    service = JobService()
    app = FastAPI()
    app.include_router(
        create_jobs_router(
            job_service=service,
            media_service=MediaService(),
            subtitle_service=SubtitleService(),
            storage_root=storage_root,
            use_real_worker=use_real_worker,
            real_worker=real_worker,
            event_service=event_service,
        ),
        prefix="/api/jobs",
    )
    return TestClient(app)


def test_create_job_accepts_video_upload_and_returns_pending_job(tmp_path):
    client = build_test_client(storage_root=tmp_path)

    response = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
        data={
            "source_language": "en",
            "target_language": "zh",
            "correct": "true",
            "asr_model": "paraformer-v2",
            "llm_model": "default",
            "subtitle_mode": "bilingual",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"].startswith("job_")
    assert payload["status"] == "pending"
    assert payload["original_filename"] == "meeting.mp4"
    assert payload["video_url"] == "/api/jobs/{0}/video".format(payload["id"])


def test_create_job_saves_uploaded_video_to_job_storage(tmp_path):
    client = build_test_client(storage_root=tmp_path)

    response = client.post(
        "/api/jobs",
        files={"file": ("meeting.webm", b"fake video", "video/webm")},
    )

    payload = response.json()
    paths = build_job_paths(payload["id"], storage_root=tmp_path, input_extension=".webm")
    assert response.status_code == 200
    assert payload["input_extension"] == ".webm"
    assert paths.input_video.read_bytes() == b"fake video"


def test_create_job_runs_mock_subtitle_job_after_response(tmp_path):
    client = build_test_client(storage_root=tmp_path)

    response = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    )

    created = response.json()
    paths = build_job_paths(created["id"], storage_root=tmp_path)
    fetched = client.get("/api/jobs/{0}".format(created["id"])).json()
    assert response.status_code == 200
    assert created["status"] == JobStatus.pending
    assert fetched["status"] == JobStatus.done
    assert fetched["progress"] == 100
    assert paths.subtitles_json.exists()
    assert paths.output_srt.exists()


def test_create_job_publishes_mock_worker_events(tmp_path):
    event_service = JobEventService()
    client = build_test_client(storage_root=tmp_path, event_service=event_service)

    response = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    )

    created = response.json()
    events = []
    while True:
        event = event_service.next_event(created["id"], timeout=0.01)
        if event is None:
            break
        events.append(event)
        if event.type == JobEventType.job_closed:
            break

    assert response.status_code == 200
    assert JobEventType.subtitle_partial in [event.type for event in events]
    assert events[-1].type == JobEventType.job_closed


def test_create_job_runs_real_worker_when_enabled(tmp_path):
    calls = []

    def fake_real_worker(
        job_id,
        paths,
        job_service,
        media_service,
        asr_service,
        llm_service,
        subtitle_service,
        event_service,
    ):
        calls.append(
            {
                "job_id": job_id,
                "paths": paths,
                "media_service": media_service,
                "asr_service": asr_service,
                "llm_service": llm_service,
                "subtitle_service": subtitle_service,
                "event_service": event_service,
            }
        )
        return job_service.update_job(
            job_id,
            status=JobStatus.done,
            progress=100,
            message="Real worker completed.",
        )

    client = build_test_client(
        storage_root=tmp_path,
        use_real_worker=True,
        real_worker=fake_real_worker,
    )

    response = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    )

    created = response.json()
    fetched = client.get("/api/jobs/{0}".format(created["id"])).json()
    assert response.status_code == 200
    assert fetched["status"] == JobStatus.done
    assert fetched["message"] == "Real worker completed."
    assert len(calls) == 1
    assert calls[0]["job_id"] == created["id"]
    assert calls[0]["event_service"] is not None


def test_read_job_video_returns_uploaded_video_file(tmp_path):
    client = build_test_client(storage_root=tmp_path)
    created = client.post(
        "/api/jobs",
        files={"file": ("meeting.webm", b"fake video", "video/webm")},
    ).json()

    response = client.get(created["video_url"])

    assert response.status_code == 200
    assert response.content == b"fake video"


def test_read_job_video_returns_404_when_file_is_missing(tmp_path):
    client = build_test_client(storage_root=tmp_path)
    created = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    ).json()
    paths = build_job_paths(created["id"], storage_root=tmp_path)
    paths.input_video.unlink()

    response = client.get(created["video_url"])

    assert response.status_code == 404
    assert response.json() == {"detail": "Video not found."}


def test_read_job_returns_created_job(tmp_path):
    client = build_test_client(storage_root=tmp_path)
    created = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    ).json()

    response = client.get("/api/jobs/{0}".format(created["id"]))

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
