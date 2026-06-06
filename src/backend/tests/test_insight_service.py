import json

import pytest

from app.core.paths import build_job_paths
from app.services.insight_service import (
    InsightService,
    InsightSourceNotFoundError,
)


def test_generate_basic_insight_reads_subtitles_and_writes_outputs(tmp_path):
    paths = build_job_paths("job_test", storage_root=tmp_path)
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
                },
                {
                    "index": 2,
                    "start": 13.78,
                    "end": 30.1,
                    "source_text": "Sweat cools the body.",
                    "target_text": "汗液可以帮助身体降温。",
                    "display_text": "Sweat cools the body.\n汗液可以帮助身体降温。",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    insight = InsightService().generate_basic_insight("job_test", storage_root=tmp_path)

    assert insight.job_id == "job_test"
    assert insight.summary == "运动会产生热量。 汗液可以帮助身体降温。"
    assert insight.markdown_url == "/api/jobs/job_test/insights/markdown"
    assert [item.title for item in insight.items] == ["片段 1", "片段 2"]
    assert insight.items[0].content == "运动会产生热量。"
    assert insight.items[0].start == 0.55
    assert insight.items[0].end == 13.51
    assert insight.items[0].source_cue_indexes == [1]

    assert paths.insight_json.exists()
    assert paths.insight_markdown.exists()
    assert json.loads(paths.insight_json.read_text(encoding="utf-8"))["job_id"] == "job_test"
    assert "# 视频知识笔记" in paths.insight_markdown.read_text(encoding="utf-8")


def test_generate_basic_insight_raises_when_subtitles_are_missing(tmp_path):
    with pytest.raises(InsightSourceNotFoundError):
        InsightService().generate_basic_insight("job_missing", storage_root=tmp_path)
