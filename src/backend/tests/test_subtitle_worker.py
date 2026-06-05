from app.core.paths import build_job_paths
from app.models.job import JobCreateOptions, JobStatus
from app.services.job_service import JobService
from app.services.subtitle_service import SubtitleService
from app.workers.subtitle_worker import run_mock_subtitle_job


def test_run_mock_subtitle_job_marks_job_done_and_writes_outputs(tmp_path):
    job_service = JobService()
    subtitle_service = SubtitleService()
    job = job_service.create_job(options=JobCreateOptions(), original_filename="input.mp4")
    paths = build_job_paths(job.id, storage_root=tmp_path)

    result = run_mock_subtitle_job(
        job_id=job.id,
        paths=paths,
        job_service=job_service,
        subtitle_service=subtitle_service,
    )

    updated = job_service.get_job(job.id)
    assert result.status == JobStatus.done
    assert updated.status == JobStatus.done
    assert updated.progress == 100
    assert paths.subtitles_json.exists()
    assert paths.output_srt.exists()
    assert "Sample source subtitle." in paths.output_srt.read_text(encoding="utf-8")
