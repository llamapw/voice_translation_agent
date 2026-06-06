from pathlib import Path

from app.core.paths import build_job_paths, get_default_storage_root


def test_default_storage_root_points_to_src_storage():
    storage_root = get_default_storage_root()

    assert storage_root == Path(__file__).resolve().parents[2] / "storage"


def test_build_job_paths_uses_job_scoped_files(tmp_path):
    paths = build_job_paths("job_123", storage_root=tmp_path, input_extension=".mov")

    assert paths.root == tmp_path / "jobs" / "job_123"
    assert paths.input_video == tmp_path / "jobs" / "job_123" / "input.mov"
    assert paths.audio_wav == tmp_path / "jobs" / "job_123" / "audio.wav"
    assert paths.subtitles_json == tmp_path / "jobs" / "job_123" / "subtitles.json"
    assert paths.output_srt == tmp_path / "jobs" / "job_123" / "output.srt"
    assert paths.insight_json == tmp_path / "jobs" / "job_123" / "insight.json"
    assert paths.insight_markdown == tmp_path / "jobs" / "job_123" / "insight.md"
