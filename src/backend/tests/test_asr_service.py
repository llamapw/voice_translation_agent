from app.models.subtitle import SubtitleCue
from app.services.asr_service import ASRService


def test_transcribe_converts_recognizer_segments_to_subtitle_cues(tmp_path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake audio")
    calls = []

    def fake_recognizer(path, model):
        calls.append((path, model))
        return [
            {
                "start": 0.0,
                "end": 1.25,
                "text": "Hello world.",
            },
            {
                "start": 1.25,
                "end": 2.5,
                "text": "Good morning.",
            },
        ]

    service = ASRService(model="custom-asr", recognizer=fake_recognizer)

    result = service.transcribe(audio_path)

    assert calls == [(audio_path, "custom-asr")]
    assert result == [
        SubtitleCue(
            index=1,
            start=0.0,
            end=1.25,
            source_text="Hello world.",
            target_text="Hello world.",
        ),
        SubtitleCue(
            index=2,
            start=1.25,
            end=2.5,
            source_text="Good morning.",
            target_text="Good morning.",
        ),
    ]


def test_transcribe_skips_empty_segments(tmp_path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake audio")

    def fake_recognizer(path, model):
        return [
            {"start": 0.0, "end": 1.0, "text": "  "},
            {"start": 1.0, "end": 2.0, "text": "Kept text."},
        ]

    service = ASRService(model="custom-asr", recognizer=fake_recognizer)

    result = service.transcribe(audio_path)

    assert len(result) == 1
    assert result[0].index == 1
    assert result[0].source_text == "Kept text."
