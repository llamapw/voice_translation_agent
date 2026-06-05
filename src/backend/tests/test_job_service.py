import pytest

from app.models.job import JobCreateOptions, JobStatus
from app.services.job_service import JobService, JobNotFoundError


def test_create_job_stores_options_and_builds_resource_urls():
    service = JobService()
    options = JobCreateOptions(source_language="ja", target_language="zh")

    job = service.create_job(options=options, original_filename="meeting.mp4")

    assert job.id.startswith("job_")
    assert job.source_language == "ja"
    assert job.target_language == "zh"
    assert job.original_filename == "meeting.mp4"
    assert job.video_url == "/api/jobs/{0}/video".format(job.id)
    assert job.subtitle_url == "/api/jobs/{0}/subtitles".format(job.id)
    assert job.srt_download_url == "/api/jobs/{0}/srt".format(job.id)


def test_get_job_returns_copy_to_protect_internal_state():
    service = JobService()
    job = service.create_job(options=JobCreateOptions(), original_filename=None)

    fetched = service.get_job(job.id)
    fetched.progress = 99

    assert service.get_job(job.id).progress == 0


def test_update_job_updates_status_progress_and_message():
    service = JobService()
    job = service.create_job(options=JobCreateOptions(), original_filename=None)

    updated = service.update_job(
        job.id,
        status=JobStatus.transcribing,
        progress=150,
        message="Transcribing audio.",
    )

    assert updated.status == JobStatus.transcribing
    assert updated.progress == 100
    assert updated.message == "Transcribing audio."


def test_fail_job_marks_job_failed_with_error():
    service = JobService()
    job = service.create_job(options=JobCreateOptions(), original_filename=None)

    failed = service.fail_job(job.id, "ASR failed")

    assert failed.status == JobStatus.failed
    assert failed.progress == 100
    assert failed.error == "ASR failed"


def test_get_unknown_job_raises_not_found_error():
    service = JobService()

    with pytest.raises(JobNotFoundError):
        service.get_job("missing")
