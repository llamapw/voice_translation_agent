import json

from app.models.subtitle import SubtitleCue
from app.services.subtitle_service import SubtitleService


def test_write_subtitles_json_writes_structured_cues(tmp_path):
    service = SubtitleService()
    path = tmp_path / "subtitles.json"
    cues = [
        SubtitleCue(
            index=1,
            start=0,
            end=1.5,
            source_text="Hello.",
            target_text="你好。",
        )
    ]

    result = service.write_subtitles_json(cues, path)

    assert result == path
    assert json.loads(path.read_text(encoding="utf-8")) == [
        {
            "index": 1,
            "start": 0,
            "end": 1.5,
            "source_text": "Hello.",
            "target_text": "你好。",
            "display_text": "Hello.\n你好。",
        }
    ]


def test_write_srt_writes_srt_text(tmp_path):
    service = SubtitleService()
    path = tmp_path / "output.srt"
    cues = [
        SubtitleCue(
            index=1,
            start=0,
            end=1,
            source_text="Hello.",
            target_text="你好。",
        )
    ]

    result = service.write_srt(cues, path)

    assert result == path
    assert path.read_text(encoding="utf-8") == (
        "1\n"
        "00:00:00,000 --> 00:00:01,000\n"
        "Hello.\n"
        "你好。\n"
    )
