import pytest
from pydantic import ValidationError

from app.models.insight import InsightItem, InsightRead


def test_insight_read_stores_summary_and_timestamped_items():
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
            )
        ],
        markdown_url="/api/jobs/job_test/insights/markdown",
    )

    assert insight.job_id == "job_test"
    assert insight.summary == "This video explains heat stress during exercise."
    assert insight.items[0].title == "Exercise produces heat"
    assert insight.items[0].start == 0.55
    assert insight.items[0].end == 13.51
    assert insight.items[0].source_cue_indexes == [1]
    assert insight.markdown_url == "/api/jobs/job_test/insights/markdown"


def test_insight_item_defaults_source_cue_indexes_to_empty_list():
    item = InsightItem(
        id="note_1",
        type="key_point",
        title="Exercise produces heat",
        content="Most exercise energy is transformed into heat.",
        start=0.55,
        end=13.51,
    )

    assert item.source_cue_indexes == []


def test_term_insight_item_can_store_source_and_target_terms():
    item = InsightItem(
        id="term_1",
        type="term",
        title="热应激",
        content="身体热量压力相关概念。",
        start=0.55,
        end=13.51,
        source_term="heat stress",
        target_term="热应激",
    )

    assert item.source_term == "heat stress"
    assert item.target_term == "热应激"


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (-0.1, 1.0),
        (1.0, -0.1),
        (2.0, 1.0),
    ],
)
def test_insight_item_rejects_invalid_time_ranges(start, end):
    with pytest.raises(ValidationError):
        InsightItem(
            id="note_1",
            type="key_point",
            title="Invalid time range",
            content="The note time range is invalid.",
            start=start,
            end=end,
        )
