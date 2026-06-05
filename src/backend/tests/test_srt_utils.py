from app.models.subtitle import SubtitleCue
from app.utils.srt import cues_to_srt, format_srt_time


def test_format_srt_time_uses_hours_minutes_seconds_and_milliseconds():
    assert format_srt_time(0) == "00:00:00,000"
    assert format_srt_time(3.25) == "00:00:03,250"
    assert format_srt_time(3661.007) == "01:01:01,007"


def test_cues_to_srt_formats_subtitle_blocks():
    cues = [
        SubtitleCue(
            index=1,
            start=0,
            end=2.5,
            source_text="Hello.",
            target_text="你好。",
        ),
        SubtitleCue(
            index=2,
            start=3,
            end=4,
            source_text="Bye.",
            target_text="再见。",
        ),
    ]

    assert cues_to_srt(cues) == (
        "1\n"
        "00:00:00,000 --> 00:00:02,500\n"
        "Hello.\n"
        "你好。\n"
        "\n"
        "2\n"
        "00:00:03,000 --> 00:00:04,000\n"
        "Bye.\n"
        "再见。\n"
    )
