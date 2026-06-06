import pytest

from app.agents.insight_agent import InsightAgent, InsightAgentError, LangChainInsightAgent
from app.models.subtitle import SubtitleCue


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeChatModel:
    def __init__(self, content: str) -> None:
        self.content = content
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return FakeMessage(self.content)


def test_insight_agent_generates_summary_and_timestamped_key_points():
    cues = [
        SubtitleCue(
            index=1,
            start=0.55,
            end=13.51,
            source_text="Exercise produces heat.",
            target_text="运动会产生热量。",
        ),
        SubtitleCue(
            index=2,
            start=13.78,
            end=30.1,
            source_text="Sweat cools the body.",
            target_text="汗液可以帮助身体降温。",
        ),
    ]

    insight = InsightAgent().generate("job_test", cues)

    assert insight.job_id == "job_test"
    assert insight.summary == "运动会产生热量。 汗液可以帮助身体降温。"
    assert insight.items[0].id == "key_point_1"
    assert insight.items[0].type == "key_point"
    assert insight.items[0].title == "片段 1"
    assert insight.items[0].content == "运动会产生热量。"
    assert insight.items[0].start == 0.55
    assert insight.items[0].end == 13.51
    assert insight.items[0].source_cue_indexes == [1]
    assert insight.markdown_url == "/api/jobs/job_test/insights/markdown"


def test_insight_agent_ignores_empty_translated_text_in_summary():
    cues = [
        SubtitleCue(
            index=1,
            start=0,
            end=1,
            source_text="No translation yet.",
            target_text="",
        ),
        SubtitleCue(
            index=2,
            start=1,
            end=2,
            source_text="Translated.",
            target_text="已有译文。",
        ),
    ]

    insight = InsightAgent().generate("job_test", cues)

    assert insight.summary == "已有译文。"


def test_langchain_insight_agent_generates_insight_from_chat_model_json():
    cues = [
        SubtitleCue(
            index=1,
            start=0.55,
            end=13.51,
            source_text="Exercise produces heat.",
            target_text="运动会产生热量。",
        )
    ]
    chat_model = FakeChatModel(
        """
        {
          "summary": "视频解释运动时的热量产生。",
          "items": [
            {
              "id": "key_point_1",
              "type": "key_point",
              "title": "运动产生热量",
              "content": "运动时大部分能量会转化为热量。",
              "start": 0.55,
              "end": 13.51,
              "source_cue_indexes": [1]
            }
          ]
        }
        """
    )

    insight = LangChainInsightAgent(chat_model=chat_model).generate("job_test", cues)

    assert insight.job_id == "job_test"
    assert insight.summary == "视频解释运动时的热量产生。"
    assert insight.items[0].title == "运动产生热量"
    assert insight.items[0].source_cue_indexes == [1]
    assert insight.markdown_url == "/api/jobs/job_test/insights/markdown"
    assert "Exercise produces heat." in chat_model.messages[1]["content"]
    assert "运动会产生热量。" in chat_model.messages[1]["content"]


def test_langchain_insight_agent_prompt_requires_term_items():
    chat_model = FakeChatModel('{"summary": "摘要", "items": []}')

    LangChainInsightAgent(chat_model=chat_model).generate("job_test", [])

    user_prompt = chat_model.messages[1]["content"]
    assert "必须提取术语" in user_prompt
    assert '"type": "term"' in user_prompt
    assert "术语 title 使用术语原词" in user_prompt


def test_langchain_insight_agent_accepts_markdown_fenced_json():
    chat_model = FakeChatModel(
        """```json
        {"summary": "摘要", "items": []}
        ```"""
    )

    insight = LangChainInsightAgent(chat_model=chat_model).generate("job_test", [])

    assert insight.summary == "摘要"
    assert insight.items == []


def test_langchain_insight_agent_raises_when_model_returns_invalid_json():
    chat_model = FakeChatModel("not json")

    with pytest.raises(InsightAgentError):
        LangChainInsightAgent(chat_model=chat_model).generate("job_test", [])
