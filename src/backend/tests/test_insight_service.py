import json

import pytest

from app.core.paths import build_job_paths
from app.models.insight import InsightRead
from app.services.insight_service import (
    ConfiguredInsightAgent,
    InsightService,
    InsightSourceNotFoundError,
    create_insight_agent,
)


class StubInsightAgent:
    def __init__(self) -> None:
        self.received_job_id = None
        self.received_cues = None

    def generate(self, job_id, cues):
        self.received_job_id = job_id
        self.received_cues = cues
        return InsightRead(
            job_id=job_id,
            summary="自定义洞察摘要。",
            items=[],
            markdown_url="/api/jobs/{0}/insights/markdown".format(job_id),
        )


class FakeLangChainInsightAgent(StubInsightAgent):
    pass


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


def test_generate_basic_insight_delegates_generation_to_agent(tmp_path):
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
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    agent = StubInsightAgent()

    insight = InsightService(agent=agent).generate_basic_insight(
        "job_test",
        storage_root=tmp_path,
    )

    assert insight.summary == "自定义洞察摘要。"
    assert agent.received_job_id == "job_test"
    assert agent.received_cues[0].target_text == "运动会产生热量。"


def test_create_insight_agent_returns_basic_agent_when_langchain_is_disabled():
    agent = create_insight_agent(use_langchain=False)

    assert agent.__class__.__name__ == "InsightAgent"


def test_create_insight_agent_returns_langchain_agent_when_enabled(monkeypatch):
    import app.services.insight_service as insight_service_module

    monkeypatch.setattr(
        insight_service_module,
        "LangChainInsightAgent",
        FakeLangChainInsightAgent,
    )

    agent = create_insight_agent(use_langchain=True)

    assert isinstance(agent, FakeLangChainInsightAgent)


def test_configured_insight_agent_defers_selected_agent_until_generate(monkeypatch):
    import app.services.insight_service as insight_service_module

    created = []

    def fake_create_insight_agent(use_langchain):
        created.append(use_langchain)
        return StubInsightAgent()

    monkeypatch.setattr(
        insight_service_module,
        "create_insight_agent",
        fake_create_insight_agent,
    )
    agent = ConfiguredInsightAgent(use_langchain=True)

    assert created == []

    insight = agent.generate("job_test", [])

    assert created == [True]
    assert insight.summary == "自定义洞察摘要。"
