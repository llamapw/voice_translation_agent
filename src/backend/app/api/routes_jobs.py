from pathlib import Path
from typing import Callable, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.paths import JobPaths, build_job_paths, get_default_storage_root
from app.models.job import JobCreateOptions, JobRead
from app.services.asr_service import ASRService, asr_service
from app.services.job_service import JobNotFoundError, JobService, job_service
from app.services.llm_service import LLMService, llm_service
from app.services.media_service import MediaService, media_service
from app.services.subtitle_service import SubtitleService, subtitle_service
from app.workers.subtitle_worker import run_mock_subtitle_job, run_subtitle_job


RealWorker = Callable[
    [
        str,
        JobPaths,
        JobService,
        MediaService,
        ASRService,
        LLMService,
        SubtitleService,
    ],
    JobRead,
]


def create_jobs_router(
    job_service: JobService,
    media_service: MediaService,
    subtitle_service: SubtitleService,
    asr_service: ASRService = asr_service,
    llm_service: LLMService = llm_service,
    storage_root: Optional[Path] = None,
    use_real_worker: bool = settings.use_real_worker,
    real_worker: RealWorker = run_subtitle_job,
) -> APIRouter:
    router = APIRouter()
    resolved_storage_root = storage_root or get_default_storage_root()

    @router.post("", response_model=JobRead)
    def create_job(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        source_language: str = Form("en"),
        target_language: str = Form("zh"),
        correct: bool = Form(True),
        asr_model: str = Form("paraformer-v2"),
        llm_model: str = Form("default"),
        subtitle_mode: str = Form("bilingual"),
    ) -> JobRead:
        options = JobCreateOptions(
            source_language=source_language,
            target_language=target_language,
            correct=correct,
            asr_model=asr_model,
            llm_model=llm_model,
            subtitle_mode=subtitle_mode,
        )
        input_extension = Path(file.filename or "input.mp4").suffix or ".mp4"
        job = job_service.create_job(
            options=options,
            original_filename=file.filename,
            input_extension=input_extension,
        )
        paths = build_job_paths(
            job.id,
            storage_root=resolved_storage_root,
            input_extension=input_extension,
        )
        media_service.save_binary_file(file.file, paths.input_video)
        if use_real_worker:
            background_tasks.add_task(
                real_worker,
                job.id,
                paths,
                job_service,
                media_service,
                asr_service,
                llm_service,
                subtitle_service,
            )
        else:
            background_tasks.add_task(
                run_mock_subtitle_job,
                job.id,
                paths,
                job_service,
                subtitle_service,
            )
        return job

    @router.get("/{job_id}", response_model=JobRead)
    def read_job(job_id: str) -> JobRead:
        try:
            return job_service.get_job(job_id)
        except JobNotFoundError:
            raise HTTPException(status_code=404, detail="Job not found.")

    @router.get("/{job_id}/video")
    def read_job_video(job_id: str) -> FileResponse:
        try:
            job = job_service.get_job(job_id)
        except JobNotFoundError:
            raise HTTPException(status_code=404, detail="Job not found.")

        path = build_job_paths(
            job.id,
            storage_root=resolved_storage_root,
            input_extension=job.input_extension,
        ).input_video
        if not path.exists():
            raise HTTPException(status_code=404, detail="Video not found.")

        return FileResponse(path=path, filename=job.original_filename or path.name)

    return router


router = create_jobs_router(
    job_service=job_service,
    media_service=media_service,
    subtitle_service=subtitle_service,
)
