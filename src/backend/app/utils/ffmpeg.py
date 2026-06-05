import subprocess
from pathlib import Path
from typing import Callable, List, Optional


class FFmpegError(RuntimeError):
    pass


Runner = Callable[..., subprocess.CompletedProcess]


def build_extract_audio_command(
    input_video: Path,
    output_audio: Path,
    ffmpeg_binary: str = "ffmpeg",
) -> List[str]:
    return [
        ffmpeg_binary,
        "-y",
        "-i",
        str(input_video),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_audio),
    ]


def extract_audio_to_wav(
    input_video: Path,
    output_audio: Path,
    ffmpeg_binary: str = "ffmpeg",
    runner: Optional[Runner] = None,
) -> Path:
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    command = build_extract_audio_command(input_video, output_audio, ffmpeg_binary)
    run_command = runner or subprocess.run

    try:
        run_command(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as error:
        detail = error.stderr or error.stdout or str(error)
        raise FFmpegError(detail) from error

    return output_audio
