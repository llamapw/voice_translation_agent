import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_insights import create_insights_router
from app.core.paths import build_job_paths
from app.services.insight_service import InsightService


def build_test_client(storage_root):
    app = FastAPI()
    app.include_router(
        create_insights_router(
            insight_service=InsightService(),
            storage_root=storage_root,
        ),
        prefix="/api/jobs",
    )
    return TestClient(app)


def write_test_subtitles(storage_root, job_id="job_test"):
    paths = build_job_paths(job_id, storage_root=storage_root)
    paths.root.mkdir(parents=True)
    paths.subtitles_json.write_text(
        json.dumps(
            [
                {
                    "index": 1,
                    "start": 0.55,
                    "end": 13.51,
                    "source_text": "Exercise produces heat.",
                    "target_text": "运动会产生热量。",
                    "display_text": "Exercise produces heat.\n运动会产生热量。",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return paths


def test_generate_insight_returns_structured_notes_and_writes_markdown(tmp_path):
    client = build_test_client(tmp_path)
    paths = write_test_subtitles(tmp_path)

    response = client.post("/api/jobs/job_test/insights")

    assert response.status_code == 200
    assert response.json()["job_id"] == "job_test"
    assert response.json()["summary"] == "运动会产生热量。"
    assert response.json()["items"][0]["title"] == "片段 1"
    assert response.json()["markdown_url"] == "/api/jobs/job_test/insights/markdown"
    assert paths.insight_markdown.exists()


def test_read_insight_returns_existing_generated_notes(tmp_path):
    client = build_test_client(tmp_path)
    write_test_subtitles(tmp_path)
    client.post("/api/jobs/job_test/insights")

    response = client.get("/api/jobs/job_test/insights")

    assert response.status_code == 200
    assert response.json()["job_id"] == "job_test"
    assert response.json()["items"][0]["content"] == "运动会产生热量。"


def test_download_insight_markdown_returns_generated_markdown(tmp_path):
    client = build_test_client(tmp_path)
    write_test_subtitles(tmp_path)
    client.post("/api/jobs/job_test/insights")

    response = client.get("/api/jobs/job_test/insights/markdown")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "# 视频知识笔记" in response.text
    assert "运动会产生热量。" in response.text


def test_generate_insight_returns_404_when_subtitles_are_missing(tmp_path):
    client = build_test_client(tmp_path)

    response = client.post("/api/jobs/missing/insights")

    assert response.status_code == 404
    assert response.json() == {"detail": "Subtitles not found."}


def test_read_insight_returns_404_when_insight_is_missing(tmp_path):
    client = build_test_client(tmp_path)

    response = client.get("/api/jobs/missing/insights")

    assert response.status_code == 404
    assert response.json() == {"detail": "Insight not found."}


def test_download_markdown_returns_404_when_markdown_is_missing(tmp_path):
    client = build_test_client(tmp_path)

    response = client.get("/api/jobs/missing/insights/markdown")

    assert response.status_code == 404
    assert response.json() == {"detail": "Insight Markdown not found."}
