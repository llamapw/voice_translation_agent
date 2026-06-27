import subprocess

import pytest

from app.utils import ffmpeg
from app.utils.ffmpeg import (
    FFmpegError,
    extract_audio_to_wav,
    resolve_ffmpeg_binary,
    stream_audio_to_wav,
)


def test_extract_audio_to_wav_runs_expected_ffmpeg_command(tmp_path):
    input_video = tmp_path / "input.mp4"
    output_audio = tmp_path / "audio.wav"
    input_video.write_bytes(b"fake video")
    calls = []

    def fake_run(command, capture_output, text, check):
        calls.append(
            {
                "command": command,
                "capture_output": capture_output,
                "text": text,
                "check": check,
            }
        )
        output_audio.write_bytes(b"fake audio")
        return subprocess.CompletedProcess(command, 0, "", "")

    result = extract_audio_to_wav(input_video, output_audio, runner=fake_run)

    assert result == output_audio
    assert calls == [
        {
            "command": [
                "ffmpeg",
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
            ],
            "capture_output": True,
            "text": True,
            "check": True,
        }
    ]


def test_extract_audio_to_wav_raises_error_when_ffmpeg_fails(tmp_path):
    input_video = tmp_path / "input.mp4"
    output_audio = tmp_path / "audio.wav"
    input_video.write_bytes(b"fake video")

    def fake_run(command, capture_output, text, check):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
            stderr="ffmpeg failed",
        )

    with pytest.raises(FFmpegError) as error:
        extract_audio_to_wav(input_video, output_audio, runner=fake_run)

    assert "ffmpeg failed" in str(error.value)


def test_stream_audio_to_wav_runs_ffmpeg_pipe_command_and_yields_chunks(tmp_path):
    input_video = tmp_path / "input.mp4"
    input_video.write_bytes(b"fake video")
    calls = []

    class FakeStdout:
        def __init__(self):
            self.chunks = [b"wav-header", b"wav-audio", b""]

        def read(self, chunk_size):
            return self.chunks.pop(0)

    class FakeStderr:
        def read(self):
            return b""

    class FakeProcess:
        def __init__(self):
            self.stdout = FakeStdout()
            self.stderr = FakeStderr()

        def wait(self):
            return 0

    def fake_popen(command, stdout, stderr, bufsize):
        calls.append(
            {
                "command": command,
                "stdout": stdout,
                "stderr": stderr,
                "bufsize": bufsize,
            }
        )
        return FakeProcess()

    chunks = list(stream_audio_to_wav(input_video, popen_factory=fake_popen))

    assert chunks == [b"wav-header", b"wav-audio"]
    assert calls == [
        {
            "command": [
                "ffmpeg",
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
            ],
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "bufsize": 0,
        }
    ]


def test_stream_audio_to_wav_raises_error_when_ffmpeg_fails(tmp_path):
    input_video = tmp_path / "input.mp4"
    input_video.write_bytes(b"fake video")

    class FakeStdout:
        def read(self, chunk_size):
            return b""

    class FakeStderr:
        def read(self):
            return b"ffmpeg failed"

    class FakeProcess:
        stdout = FakeStdout()
        stderr = FakeStderr()

        def wait(self):
            return 1

    def fake_popen(command, stdout, stderr, bufsize):
        return FakeProcess()

    with pytest.raises(FFmpegError) as error:
        list(stream_audio_to_wav(input_video, popen_factory=fake_popen))

    assert "ffmpeg failed" in str(error.value)


def test_resolve_ffmpeg_binary_falls_back_to_imageio_ffmpeg(monkeypatch):
    monkeypatch.setattr(ffmpeg.shutil, "which", lambda binary: None)

    class FakeImageioFFmpeg:
        @staticmethod
        def get_ffmpeg_exe():
            return "embedded-ffmpeg.exe"

    result = resolve_ffmpeg_binary(
        "ffmpeg",
        imageio_ffmpeg_module=FakeImageioFFmpeg,
    )

    assert result == "embedded-ffmpeg.exe"


def test_resolve_ffmpeg_binary_raises_clear_error_when_unavailable(monkeypatch):
    monkeypatch.setattr(ffmpeg.shutil, "which", lambda binary: None)

    with pytest.raises(FFmpegError) as error:
        resolve_ffmpeg_binary("ffmpeg", imageio_ffmpeg_module=None)

    assert "FFmpeg executable not found" in str(error.value)
