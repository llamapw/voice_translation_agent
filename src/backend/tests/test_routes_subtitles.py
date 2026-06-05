from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_subtitles import create_subtitles_router
from app.core.paths import build_job_paths
from app.models.subtitle import SubtitleCue
from app.services.subtitle_service import SubtitleService


def build_test_client(storage_root):
    app = FastAPI()
    app.include_router(create_subtitles_router(storage_root=storage_root), prefix="/api/jobs")
    return TestClient(app)


def test_read_subtitles_returns_job_subtitle_cues(tmp_path):
    client = build_test_client(tmp_path)
    paths = build_job_paths("job_001", storage_root=tmp_path)
    SubtitleService().write_subtitles_json(
        [
            SubtitleCue(
                index=1,
                start=0,
                end=1.5,
                source_text="Hello.",
                target_text="你好。",
            )
        ],
        paths.subtitles_json,
    )

    response = client.get("/api/jobs/job_001/subtitles")

    assert response.status_code == 200
    assert response.json() == [
        {
            "index": 1,
            "start": 0.0,
            "end": 1.5,
            "source_text": "Hello.",
            "target_text": "你好。",
            "display_text": "Hello.\n你好。",
        }
    ]


def test_download_srt_returns_job_srt_file(tmp_path):
    client = build_test_client(tmp_path)
    paths = build_job_paths("job_001", storage_root=tmp_path)
    SubtitleService().write_srt(
        [
            SubtitleCue(
                index=1,
                start=0,
                end=1,
                source_text="Hello.",
                target_text="你好。",
            )
        ],
        paths.output_srt,
    )

    response = client.get("/api/jobs/job_001/srt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-subrip")
    assert response.text == (
        "1\n"
        "00:00:00,000 --> 00:00:01,000\n"
        "Hello.\n"
        "你好。\n"
    )


def test_read_subtitles_returns_404_when_file_is_missing(tmp_path):
    client = build_test_client(tmp_path)

    response = client.get("/api/jobs/missing/subtitles")

    assert response.status_code == 404
    assert response.json() == {"detail": "Subtitles not found."}


def test_download_srt_returns_404_when_file_is_missing(tmp_path):
    client = build_test_client(tmp_path)

    response = client.get("/api/jobs/missing/srt")

    assert response.status_code == 404
    assert response.json() == {"detail": "SRT not found."}
