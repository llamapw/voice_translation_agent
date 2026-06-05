from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_jobs import create_jobs_router
from app.core.paths import build_job_paths
from app.services.media_service import MediaService
from app.services.job_service import JobService


def build_test_client(storage_root=None) -> TestClient:
    service = JobService()
    app = FastAPI()
    app.include_router(
        create_jobs_router(
            job_service=service,
            media_service=MediaService(),
            storage_root=storage_root,
        ),
        prefix="/api/jobs",
    )
    return TestClient(app)


def test_create_job_accepts_video_upload_and_returns_pending_job():
    client = build_test_client()

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
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    )

    payload = response.json()
    paths = build_job_paths(payload["id"], storage_root=tmp_path, input_extension=".mp4")
    assert response.status_code == 200
    assert paths.input_video.read_bytes() == b"fake video"


def test_read_job_returns_created_job():
    client = build_test_client()
    created = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    ).json()

    response = client.get("/api/jobs/{0}".format(created["id"]))

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
