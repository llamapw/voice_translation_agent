from io import BytesIO

from app.services.media_service import MediaService


def test_save_binary_file_writes_stream_to_destination(tmp_path):
    service = MediaService()
    destination = tmp_path / "jobs" / "job_001" / "input.mp4"

    result = service.save_binary_file(BytesIO(b"fake video"), destination)

    assert result == destination
    assert destination.read_bytes() == b"fake video"


def test_extract_audio_calls_configured_audio_extractor(tmp_path):
    input_video = tmp_path / "jobs" / "job_001" / "input.mp4"
    output_audio = tmp_path / "jobs" / "job_001" / "audio.wav"
    calls = []

    def fake_extract_audio(input_path, output_path, ffmpeg_binary):
        calls.append((input_path, output_path, ffmpeg_binary))
        output_path.write_bytes(b"fake audio")
        return output_path

    service = MediaService(
        ffmpeg_binary="custom-ffmpeg",
        audio_extractor=fake_extract_audio,
    )

    result = service.extract_audio(input_video, output_audio)

    assert result == output_audio
    assert output_audio.read_bytes() == b"fake audio"
    assert calls == [(input_video, output_audio, "custom-ffmpeg")]
