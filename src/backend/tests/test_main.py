from fastapi.testclient import TestClient

from app.core.paths import build_job_paths
from app.main import app, create_app


def test_health_endpoint_returns_service_status():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "voice_translation_agent",
    }


def test_app_registers_jobs_api_router_and_uses_configured_storage(tmp_path):
    client = TestClient(create_app(storage_root=tmp_path))

    response = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    )

    payload = response.json()
    paths = build_job_paths(payload["id"], storage_root=tmp_path)
    assert response.status_code == 200
    assert payload["status"] == "pending"
    assert paths.input_video.read_bytes() == b"fake video"


def test_app_upload_job_generates_mock_subtitles(tmp_path):
    client = TestClient(create_app(storage_root=tmp_path))

    created = client.post(
        "/api/jobs",
        files={"file": ("meeting.mp4", b"fake video", "video/mp4")},
    ).json()

    subtitles_response = client.get(created["subtitle_url"])
    srt_response = client.get(created["srt_download_url"])

    assert subtitles_response.status_code == 200
    assert subtitles_response.json()[0]["source_text"] == "Sample source subtitle."
    assert srt_response.status_code == 200
    assert "Sample source subtitle." in srt_response.text


def test_app_registers_subtitles_api_router():
    client = TestClient(app)

    response = client.get("/api/jobs/missing/subtitles")

    assert response.status_code == 404
    assert response.json() == {"detail": "Subtitles not found."}
