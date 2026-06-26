import subprocess

import pytest

from app.utils import ffmpeg
from app.utils.ffmpeg import FFmpegError, extract_audio_to_wav, resolve_ffmpeg_binary


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
