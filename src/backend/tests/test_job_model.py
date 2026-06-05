from app.models.job import JobCreateOptions, JobRead, JobStatus


def test_job_status_contains_expected_processing_states():
    assert [status.value for status in JobStatus] == [
        "pending",
        "extracting_audio",
        "transcribing",
        "correcting",
        "translating",
        "generating_subtitle",
        "done",
        "failed",
    ]


def test_job_create_options_provides_defaults():
    options = JobCreateOptions()

    assert options.source_language == "en"
    assert options.target_language == "zh"
    assert options.correct is True
    assert options.asr_model == "paraformer-v2"
    assert options.llm_model == "default"
    assert options.subtitle_mode == "bilingual"


def test_job_read_defaults_to_pending_task():
    job = JobRead()

    assert job.id.startswith("job_")
    assert job.status == JobStatus.pending
    assert job.progress == 0
    assert job.message == "Task is waiting to start."
    assert job.error is None
