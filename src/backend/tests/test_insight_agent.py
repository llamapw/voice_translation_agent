from app.agents.insight_agent import InsightAgent
from app.models.subtitle import SubtitleCue


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
