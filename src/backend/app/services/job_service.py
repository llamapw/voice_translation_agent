from threading import Lock
from typing import Dict, Optional

from app.models.job import JobCreateOptions, JobRead, JobStatus


class JobNotFoundError(KeyError):
    pass


class JobService:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRead] = {}
        self._lock = Lock()

    def create_job(
        self,
        options: JobCreateOptions,
        original_filename: Optional[str],
        input_extension: str = ".mp4",
    ) -> JobRead:
        job = JobRead(
            source_language=options.source_language,
            target_language=options.target_language,
            correct=options.correct,
            asr_model=options.asr_model,
            llm_model=options.llm_model,
            subtitle_mode=options.subtitle_mode,
            original_filename=original_filename,
            input_extension=input_extension,
        )
        job.video_url = "/api/jobs/{0}/video".format(job.id)
        job.subtitle_url = "/api/jobs/{0}/subtitles".format(job.id)
        job.srt_download_url = "/api/jobs/{0}/srt".format(job.id)

        with self._lock:
            self._jobs[job.id] = job

        return job.model_copy()

    def get_job(self, job_id: str) -> JobRead:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)
            return job.model_copy()

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> JobRead:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFoundError(job_id)

            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = max(0, min(progress, 100))
            if message is not None:
                job.message = message
            if error is not None:
                job.error = error

            self._jobs[job.id] = job
            return job.model_copy()

    def fail_job(self, job_id: str, error: str) -> JobRead:
        return self.update_job(
            job_id,
            status=JobStatus.failed,
            progress=100,
            message="Task failed.",
            error=error,
        )


job_service = JobService()
