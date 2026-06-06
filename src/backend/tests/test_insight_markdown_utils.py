from app.models.insight import InsightItem, InsightRead
from app.utils.insight_markdown import render_insight_markdown


def test_render_insight_markdown_includes_summary_and_timestamped_items():
    insight = InsightRead(
        job_id="job_test",
        summary="This video explains heat stress during exercise.",
        items=[
            InsightItem(
                id="note_1",
                type="key_point",
                title="Exercise produces heat",
                content="Most exercise energy is transformed into heat.",
                start=0.55,
                end=13.51,
                source_cue_indexes=[1],
            ),
            InsightItem(
                id="term_1",
                type="term",
                title="可补偿热应激",
                content="身体可以及时散热的状态。",
                source_term="Compensable heat stress",
                target_term="可补偿热应激",
                start=4.0,
                end=10.0,
            ),
        ],
    )

    markdown = render_insight_markdown(insight)

    assert "# 视频知识笔记" in markdown
    assert "任务 ID: `job_test`" in markdown
    assert "## 摘要" in markdown
    assert "This video explains heat stress during exercise." in markdown
    assert "## 关键要点" in markdown
    assert "- [00:00.550] **Exercise produces heat**" in markdown
    assert "  Most exercise energy is transformed into heat." in markdown
    assert "  来源字幕: 1" in markdown
    assert "## 术语" in markdown
    assert "- [00:04.000] **Compensable heat stress / 可补偿热应激**" in markdown
    assert "  身体可以及时散热的状态。" in markdown
