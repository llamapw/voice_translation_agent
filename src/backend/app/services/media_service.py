import shutil
from pathlib import Path
from typing import BinaryIO, Callable, Iterator, Optional

from app.core.config import settings
from app.utils.ffmpeg import extract_audio_to_wav, stream_audio_to_wav


AudioExtractor = Callable[[Path, Path, str], Path]
AudioStreamer = Callable[[Path, str], Iterator[bytes]]


class MediaService:
    def __init__(
        self,
        ffmpeg_binary: str = settings.ffmpeg_binary,
        audio_extractor: Optional[AudioExtractor] = None,
        audio_streamer: Optional[AudioStreamer] = None,
    ) -> None:
        self._ffmpeg_binary = ffmpeg_binary
        self._audio_extractor = audio_extractor or extract_audio_to_wav
        self._audio_streamer = audio_streamer or stream_audio_to_wav

    def save_binary_file(self, source: BinaryIO, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            shutil.copyfileobj(source, output)
        return destination

    def extract_audio(self, input_video: Path, output_audio: Path) -> Path:
        output_audio.parent.mkdir(parents=True, exist_ok=True)
        return self._audio_extractor(
            input_video,
            output_audio,
            self._ffmpeg_binary,
        )

    def stream_audio(self, input_video: Path, output_audio: Path) -> Iterator[bytes]:
        output_audio.parent.mkdir(parents=True, exist_ok=True)
        return self._audio_streamer(input_video, self._ffmpeg_binary)


media_service = MediaService()
