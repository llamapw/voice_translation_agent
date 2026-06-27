import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Iterator, List, Optional


class FFmpegError(RuntimeError):
    pass


Runner = Callable[..., subprocess.CompletedProcess]
PopenFactory = Callable[..., subprocess.Popen]
_DEFAULT_IMAGEIO_FFMPEG = object()


def resolve_ffmpeg_binary(
    ffmpeg_binary: str = "ffmpeg",
    imageio_ffmpeg_module: Any = _DEFAULT_IMAGEIO_FFMPEG,
) -> str:
    ffmpeg_path = Path(ffmpeg_binary)
    if ffmpeg_path.exists():
        return str(ffmpeg_path)

    resolved_binary = shutil.which(ffmpeg_binary)
    if resolved_binary:
        return resolved_binary

    if imageio_ffmpeg_module is _DEFAULT_IMAGEIO_FFMPEG:
        try:
            import imageio_ffmpeg
        except ImportError:
            imageio_ffmpeg_module = None
        else:
            imageio_ffmpeg_module = imageio_ffmpeg

    if imageio_ffmpeg_module is not None:
        return imageio_ffmpeg_module.get_ffmpeg_exe()

    raise FFmpegError(
        "FFmpeg executable not found. Set FFMPEG_BINARY in .env, "
        "add ffmpeg to PATH, or install imageio-ffmpeg."
    )


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
        "-f",
        "wav",
        str(output_audio),
    ]


def build_stream_audio_command(
    input_video: Path,
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
        "-f",
        "wav",
        "pipe:1",
    ]


def extract_audio_to_wav(
    input_video: Path,
    output_audio: Path,
    ffmpeg_binary: str = "ffmpeg",
    runner: Optional[Runner] = None,
) -> Path:
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    run_command = runner or subprocess.run
    resolved_ffmpeg = ffmpeg_binary if runner else resolve_ffmpeg_binary(ffmpeg_binary)
    command = build_extract_audio_command(input_video, output_audio, resolved_ffmpeg)

    try:
        run_command(command, capture_output=True, text=True, check=True)
    except FileNotFoundError as error:
        raise FFmpegError(
            "FFmpeg executable not found. Set FFMPEG_BINARY in .env, "
            "add ffmpeg to PATH, or install imageio-ffmpeg."
        ) from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr or error.stdout or str(error)
        raise FFmpegError(detail) from error

    return output_audio


def stream_audio_to_wav(
    input_video: Path,
    ffmpeg_binary: str = "ffmpeg",
    popen_factory: Optional[PopenFactory] = None,
    chunk_size: int = 3200,
) -> Iterator[bytes]:
    resolved_ffmpeg = (
        ffmpeg_binary if popen_factory else resolve_ffmpeg_binary(ffmpeg_binary)
    )
    command = build_stream_audio_command(input_video, resolved_ffmpeg)
    popen = popen_factory or subprocess.Popen

    try:
        process = popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
    except FileNotFoundError as error:
        raise FFmpegError(
            "FFmpeg executable not found. Set FFMPEG_BINARY in .env, "
            "add ffmpeg to PATH, or install imageio-ffmpeg."
        ) from error

    assert process.stdout is not None
    while True:
        chunk = process.stdout.read(chunk_size)
        if not chunk:
            break
        yield chunk

    return_code = process.wait()
    if return_code != 0:
        stderr = process.stderr.read() if process.stderr is not None else b""
        detail = stderr.decode("utf-8", errors="replace") or "ffmpeg failed"
        raise FFmpegError(detail)
