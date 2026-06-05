from app.models.subtitle import SubtitleCue


def test_subtitle_cue_stores_timed_source_and_target_text():
    cue = SubtitleCue(
        index=1,
        start=0.5,
        end=3.25,
        source_text="Hello world.",
        target_text="你好，世界。",
        display_text="Hello world.\n你好，世界。",
    )

    assert cue.index == 1
    assert cue.start == 0.5
    assert cue.end == 3.25
    assert cue.source_text == "Hello world."
    assert cue.target_text == "你好，世界。"
    assert cue.display_text == "Hello world.\n你好，世界。"


def test_subtitle_cue_builds_display_text_when_not_provided():
    cue = SubtitleCue(
        index=2,
        start=4.0,
        end=6.0,
        source_text="Good morning.",
        target_text="早上好。",
    )

    assert cue.display_text == "Good morning.\n早上好。"
