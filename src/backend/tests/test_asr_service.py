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


def test_transcribe_publishes_cues_from_streaming_segments(tmp_path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake audio")
    streamed_cues = []

    def fake_recognizer(path, model, on_segment=None):
        if on_segment is not None:
            on_segment({"start": 0.0, "end": 1.25, "text": "First sentence."})
            on_segment({"start": 1.25, "end": 2.5, "text": "Second sentence."})
        return []

    service = ASRService(model="custom-asr", recognizer=fake_recognizer)

    result = service.transcribe(audio_path, on_cue=streamed_cues.append)

    assert result == streamed_cues
    assert [cue.index for cue in streamed_cues] == [1, 2]
    assert [cue.source_text for cue in streamed_cues] == [
        "First sentence.",
        "Second sentence.",
    ]


def test_transcribe_streams_interim_segments_without_returning_them(tmp_path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake audio")
    streamed_cues = []

    def fake_recognizer(path, model, on_segment=None):
        if on_segment is not None:
            on_segment(
                {
                    "index": 1,
                    "start": 0.0,
                    "end": 0.5,
                    "text": "First",
                    "is_final": False,
                }
            )
            on_segment(
                {
                    "index": 1,
                    "start": 0.0,
                    "end": 1.25,
                    "text": "First sentence.",
                    "is_final": True,
                }
            )
            on_segment(
                {
                    "index": 2,
                    "start": 1.25,
                    "end": 2.5,
                    "text": "Second sentence.",
                    "is_final": True,
                }
            )
        return []

    service = ASRService(model="custom-asr", recognizer=fake_recognizer)

    result = service.transcribe(audio_path, on_cue=streamed_cues.append)

    assert [cue.source_text for cue in streamed_cues] == [
        "First",
        "First sentence.",
        "Second sentence.",
    ]
    assert [cue.index for cue in streamed_cues] == [1, 1, 2]
    assert [cue.source_text for cue in result] == [
        "First sentence.",
        "Second sentence.",
    ]
