from io import BytesIO

from app.services.media_service import MediaService


def test_save_binary_file_writes_stream_to_destination(tmp_path):
    service = MediaService()
    destination = tmp_path / "jobs" / "job_001" / "input.mp4"

    result = service.save_binary_file(BytesIO(b"fake video"), destination)

    assert result == destination
    assert destination.read_bytes() == b"fake video"
