from app.models.job import SubtitleMode
from app.models.subtitle import SubtitleCue
from app.services.llm_service import LLMService


def test_enrich_subtitles_corrects_source_and_translates_target_for_bilingual_mode():
    calls = []

    def fake_completion(prompt, model):
        calls.append((prompt, model))
        if "最终输出必须全部使用简体中文" in prompt:
            return "你好，世界。"
        return "Hello, world."

    service = LLMService(model="custom-llm", text_generator=fake_completion)
    cues = [
        SubtitleCue(
            index=1,
            start=0.0,
            end=1.0,
            source_text="helo world",
            target_text="helo world",
        )
    ]

    result = service.enrich_subtitles(
        cues,
        correct=True,
        target_language="zh",
        subtitle_mode="bilingual",
    )

    assert result == [
        SubtitleCue(
            index=1,
            start=0.0,
            end=1.0,
            source_text="Hello, world.",
            target_text="你好，世界。",
        )
    ]
    assert len(calls) == 2
    assert calls[0][1] == "custom-llm"
    assert "请纠正以下字幕文本" in calls[0][0]
    assert "请处理以下字幕文本" in calls[1][0]


def test_enrich_subtitles_returns_original_cues_when_no_llm_work_is_requested():
    calls = []

    def fake_completion(prompt, model):
        calls.append((prompt, model))
        return "unused"

    service = LLMService(text_generator=fake_completion)
    cues = [
        SubtitleCue(
            index=1,
            start=0.0,
            end=1.0,
            source_text="Hello.",
            target_text="Hello.",
        )
    ]

    result = service.enrich_subtitles(
        cues,
        correct=False,
        target_language="",
        subtitle_mode="source",
    )

    assert result == cues
    assert calls == []


def test_enrich_subtitles_calls_callback_for_each_enriched_cue():
    emitted = []

    def fake_completion(prompt, model):
        if "最终输出必须全部使用简体中文" in prompt:
            return "你好。"
        return "Hello."

    service = LLMService(text_generator=fake_completion)
    cues = [
        SubtitleCue(
            index=1,
            start=0.0,
            end=1.0,
            source_text="helo",
            target_text="helo",
        ),
        SubtitleCue(
            index=2,
            start=1.0,
            end=2.0,
            source_text="world",
            target_text="world",
        ),
    ]

    result = service.enrich_subtitles(
        cues,
        correct=True,
        target_language="zh",
        subtitle_mode="bilingual",
        on_cue=emitted.append,
    )

    assert emitted == result
    assert [cue.index for cue in emitted] == [1, 2]
