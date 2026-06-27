import time
from inspect import signature
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from app.core.config import settings
from app.models.subtitle import SubtitleCue


ASRSegment = Dict[str, object]
SegmentCallback = Callable[[ASRSegment], None]
Recognizer = Callable[..., List[ASRSegment]]
StreamRecognizer = Callable[..., List[ASRSegment]]
CueCallback = Callable[[SubtitleCue], None]


class ASRError(RuntimeError):
    pass


class ASRService:
    def __init__(
        self,
        model: str = settings.asr_model,
        recognizer: Optional[Recognizer] = None,
        stream_recognizer: Optional[StreamRecognizer] = None,
    ) -> None:
        self._model = model
        self._recognizer = recognizer or recognize_audio_with_fun_asr
        self._stream_recognizer = stream_recognizer or recognize_wav_stream_with_fun_asr

    def transcribe(
        self,
        audio_path: Path,
        on_cue: Optional[CueCallback] = None,
    ) -> List[SubtitleCue]:
        if audio_path.suffix.lower() != ".wav":
            raise ASRError(
                "Streaming ASR input must be a WAV file, got: {0}".format(audio_path)
            )

        return self._transcribe_segments(audio_path, on_cue)

    def transcribe_wav_stream(
        self,
        audio_chunks: Iterable[bytes],
        on_cue: Optional[CueCallback] = None,
    ) -> List[SubtitleCue]:
        return self._transcribe_segments(audio_chunks, on_cue, recognizer=self._stream_recognizer)

    def _transcribe_segments(
        self,
        audio_input,
        on_cue: Optional[CueCallback] = None,
        recognizer: Optional[Recognizer] = None,
    ) -> List[SubtitleCue]:
        selected_recognizer = recognizer or self._recognizer
        cues = []

        def append_segment(segment: ASRSegment) -> None:
            text = str(segment.get("text", "")).strip()
            if not text:
                return

            is_final = bool(segment.get("is_final", True))
            cue_index = int(segment.get("index", len(cues) + 1))
            cue = SubtitleCue(
                index=cue_index,
                start=float(segment.get("start", 0.0)),
                end=float(segment.get("end", 0.0)),
                source_text=text,
                target_text=text,
            )
            if on_cue is not None:
                on_cue(cue)
            if not is_final:
                return

            existing_index = next(
                (index for index, item in enumerate(cues) if item.index == cue.index),
                None,
            )
            if existing_index is None:
                cues.append(cue)
            else:
                cues[existing_index] = cue

        if _supports_streaming_callback(selected_recognizer):
            segments = selected_recognizer(audio_input, self._model, append_segment)
        else:
            segments = selected_recognizer(audio_input, self._model)

        streamed_count = len(cues)
        for segment in segments[streamed_count:]:
            append_segment(segment)

        return cues


def _require_dashscope_api_key() -> str:
    if not settings.dashscope_api_key:
        raise ASRError("Missing DASHSCOPE_API_KEY.")
    return settings.dashscope_api_key


def _supports_streaming_callback(recognizer: Recognizer) -> bool:
    parameters = signature(recognizer).parameters.values()
    return any(parameter.kind == parameter.VAR_POSITIONAL for parameter in parameters) or len(
        list(signature(recognizer).parameters)
    ) >= 3


def recognize_audio_with_fun_asr(
    audio_path: Path,
    model: str,
    on_segment: Optional[SegmentCallback] = None,
) -> List[ASRSegment]:
    file_buffer = audio_path.read_bytes()
    if not file_buffer:
        raise ASRError("Audio file is empty: {0}".format(audio_path))

    return recognize_wav_stream_with_fun_asr(
        _iter_audio_chunks(file_buffer),
        model,
        on_segment,
    )


def _iter_audio_chunks(file_buffer: bytes, chunk_size: int = 3200) -> Iterable[bytes]:
    offset = 0
    while offset < len(file_buffer):
        yield file_buffer[offset : offset + chunk_size]
        offset += chunk_size


def recognize_wav_stream_with_fun_asr(
    audio_chunks: Iterable[bytes],
    model: str,
    on_segment: Optional[SegmentCallback] = None,
) -> List[ASRSegment]:
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
                if not item:
                    continue

                text = item.get("text", "").strip()
                if not text:
                    continue

                begin_ms = item.get("begin_time")
                if begin_ms is None:
                    begin_ms = self.last_end_ms

                end_ms = item.get("end_time")
                if end_ms is None:
                    end_ms = begin_ms + 500
                is_final = RecognitionResult.is_sentence_end(item)
                segment = {
                    "index": len(self.segments) + 1,
                    "start": begin_ms / 1000,
                    "end": max(end_ms / 1000, begin_ms / 1000 + 0.5),
                    "text": text,
                    "is_final": is_final,
                }
                if on_segment is not None:
                    on_segment(segment)
                if not is_final:
                    continue

                self.last_end_ms = end_ms
                self.segments.append(segment)

    callback = SubtitleRecognitionCallback()
    recognition = Recognition(
        model=model,
        format="wav",
        sample_rate=16000,
        callback=callback,
    )
    recognition.start()

    sent_any_audio = False
    for audio_data in audio_chunks:
        if not audio_data:
            continue
        sent_any_audio = True
        try:
            recognition.send_audio_frame(audio_data)
        except Exception as error:
            callback.error_message = str(error)
            break
        time.sleep(0.1)

    recognition.stop()

    if not sent_any_audio:
        raise ASRError("Audio stream is empty.")

    if callback.error_message:
        raise ASRError(callback.error_message)

    return callback.segments


asr_service = ASRService()
