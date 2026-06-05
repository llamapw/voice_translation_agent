import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from app.core.config import settings
from app.models.subtitle import SubtitleCue


ASRSegment = Dict[str, object]
Recognizer = Callable[[Path, str], List[ASRSegment]]


class ASRError(RuntimeError):
    pass


class ASRService:
    def __init__(
        self,
        model: str = settings.asr_model,
        recognizer: Optional[Recognizer] = None,
    ) -> None:
        self._model = model
        self._recognizer = recognizer or recognize_audio_with_fun_asr

    def transcribe(self, audio_path: Path) -> List[SubtitleCue]:
        segments = self._recognizer(audio_path, self._model)
        cues = []
        for segment in segments:
            text = str(segment.get("text", "")).strip()
            if not text:
                continue

            cues.append(
                SubtitleCue(
                    index=len(cues) + 1,
                    start=float(segment.get("start", 0.0)),
                    end=float(segment.get("end", 0.0)),
                    source_text=text,
                    target_text=text,
                )
            )

        return cues


def _require_dashscope_api_key() -> str:
    if not settings.dashscope_api_key:
        raise ASRError("Missing DASHSCOPE_API_KEY.")
    return settings.dashscope_api_key


def recognize_audio_with_fun_asr(audio_path: Path, model: str) -> List[ASRSegment]:
    try:
        import dashscope
        from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult
    except ImportError as error:
        raise ASRError("Missing dashscope dependency.") from error

    dashscope.api_key = _require_dashscope_api_key()
    dashscope.base_websocket_api_url = settings.dashscope_websocket_url

    class SubtitleRecognitionCallback(RecognitionCallback):
        def __init__(self) -> None:
            self.error_message = None
            self.last_end_ms = 0
            self.segments = []

        def on_error(self, result) -> None:
            self.error_message = result.message

        def on_event(self, result) -> None:
            sentence = result.get_sentence()
            sentences = sentence if isinstance(sentence, list) else [sentence]
            for item in sentences:
                if not item or not RecognitionResult.is_sentence_end(item):
                    continue

                text = item.get("text", "").strip()
                end_ms = item.get("end_time")
                if not text or end_ms is None:
                    continue

                begin_ms = item.get("begin_time")
                if begin_ms is None:
                    begin_ms = self.last_end_ms

                self.last_end_ms = end_ms
                self.segments.append(
                    {
                        "start": begin_ms / 1000,
                        "end": max(end_ms / 1000, begin_ms / 1000 + 0.5),
                        "text": text,
                    }
                )

    file_buffer = audio_path.read_bytes()
    if not file_buffer:
        raise ASRError("Audio file is empty: {0}".format(audio_path))

    callback = SubtitleRecognitionCallback()
    recognition = Recognition(
        model=model,
        format=audio_path.suffix.lower().lstrip("."),
        sample_rate=16000,
        callback=callback,
    )
    recognition.start()

    offset = 0
    chunk_size = 3200
    while offset < len(file_buffer) and not callback.error_message:
        audio_data = file_buffer[offset : offset + chunk_size]
        try:
            recognition.send_audio_frame(audio_data)
        except Exception as error:
            callback.error_message = str(error)
            break
        offset += chunk_size
        time.sleep(0.1)

    recognition.stop()

    if callback.error_message:
        raise ASRError(callback.error_message)

    return callback.segments


asr_service = ASRService()
