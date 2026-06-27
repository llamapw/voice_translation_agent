from typing import Callable, Iterator, List, Optional

from app.core.config import settings
from app.models.job import SubtitleMode
from app.models.subtitle import SubtitleCue


TextGenerator = Callable[[str, str], str]
StreamTextGenerator = Callable[[str, str], Iterator[str]]
CueCallback = Callable[[SubtitleCue], None]
DeltaCallback = Callable[[str], None]


class LLMError(RuntimeError):
    pass


def get_language_name(language: str) -> str:
    language_map = {
        "zh": "简体中文",
        "zh-cn": "简体中文",
        "en": "英文",
        "ja": "日文",
        "ko": "韩文",
    }
    return language_map.get(language.lower(), language)


class LLMService:
    def __init__(
        self,
        model: str = settings.llm_model,
        text_generator: Optional[TextGenerator] = None,
        stream_text_generator: Optional[StreamTextGenerator] = None,
    ) -> None:
        self._model = model
        self._text_generator = text_generator or generate_text_with_openai
        self._stream_text_generator = stream_text_generator or stream_text_with_openai

    def enrich_subtitles(
        self,
        cues: List[SubtitleCue],
        correct: bool,
        source_language: str,
        target_language: str,
        subtitle_mode: SubtitleMode,
        on_cue: Optional[CueCallback] = None,
    ) -> List[SubtitleCue]:
        enriched = []
        for cue in cues:
            source_text = cue.source_text
            target_text = cue.target_text

            if correct:
                source_text = self._text_generator(
                    build_correction_prompt(cue.source_text, source_language),
                    self._model,
                )

            if subtitle_mode in ("target", "bilingual") and target_language:
                target_text = self._text_generator(
                    build_translation_prompt(cue.source_text, target_language),
                    self._model,
                )
            elif subtitle_mode == "source":
                target_text = source_text

            enriched_cue = SubtitleCue(
                index=cue.index,
                start=cue.start,
                end=cue.end,
                source_text=source_text,
                target_text=target_text,
            )
            enriched.append(enriched_cue)
            if on_cue is not None:
                on_cue(enriched_cue)

        return enriched

    def stream_enriched_subtitle(
        self,
        cue: SubtitleCue,
        correct: bool,
        source_language: str,
        target_language: str,
        subtitle_mode: SubtitleMode,
        on_delta: Optional[DeltaCallback] = None,
    ) -> SubtitleCue:
        source_text = cue.source_text
        target_text = cue.target_text

        if correct:
            source_text = self._text_generator(
                build_correction_prompt(cue.source_text, source_language),
                self._model,
            )

        if subtitle_mode in ("target", "bilingual") and target_language:
            chunks = []
            for delta in self._stream_text_generator(
                build_translation_prompt(cue.source_text, target_language),
                self._model,
            ):
                chunks.append(delta)
                if on_delta is not None:
                    on_delta(delta)
            target_text = "".join(chunks).strip()
        elif subtitle_mode == "source":
            target_text = source_text

        return SubtitleCue(
            index=cue.index,
            start=cue.start,
            end=cue.end,
            source_text=source_text,
            target_text=target_text,
        )


def build_correction_prompt(text: str, source_language: str = "") -> str:
    language_name = get_language_name(source_language) if source_language else "原语种"
    return (
        "你是字幕文本校对助手。请纠正 ASR 或翻译造成的错别字、同音误识别、"
        "标点和断句问题。保持原意，不扩写，不解释。"
        "最终输出必须全部使用{language_name}，不要翻译成其他语言。\n"
        "请纠正以下字幕文本:\n{text}"
    ).format(language_name=language_name, text=text)


def build_translation_prompt(text: str, target_language: str) -> str:
    language_name = get_language_name(target_language)
    return (
        "你是字幕翻译和校对助手。请先纠正 ASR 造成的错别字、同音误识别、"
        "断句和标点问题，然后将字幕完整翻译为{0}。"
        "最终输出必须全部使用{0}，不要解释，不要添加编号，不要保留原文。\n"
        "请处理以下字幕文本:\n{1}".format(language_name, text)
    )


def generate_text_with_openai(prompt: str, model: str) -> str:
    if not settings.llm_api_key:
        raise LLMError("Missing LLM_API_KEY.")

    try:
        from openai import OpenAI
    except ImportError as error:
        raise LLMError("Missing openai dependency.") from error

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=1024,
        temperature=0,
    )
    content = completion.choices[0].message.content
    if not content:
        raise LLMError("LLM returned empty content.")
    return content.strip()


def stream_text_with_openai(prompt: str, model: str) -> Iterator[str]:
    if not settings.llm_api_key:
        raise LLMError("Missing LLM_API_KEY.")

    try:
        from openai import OpenAI
    except ImportError as error:
        raise LLMError("Missing openai dependency.") from error

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=1024,
        temperature=0,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


llm_service = LLMService()
