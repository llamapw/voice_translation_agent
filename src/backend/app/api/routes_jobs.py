from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.job import JobCreateOptions, JobRead
from app.services.job_service import JobNotFoundError, JobService, job_service


def create_jobs_router(service: JobService) -> APIRouter:
    router = APIRouter()

    @router.post("", response_model=JobRead)
    def create_job(
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
        return service.create_job(options=options, original_filename=file.filename)

    @router.get("/{job_id}", response_model=JobRead)
    def read_job(job_id: str) -> JobRead:
        try:
            return service.get_job(job_id)
        except JobNotFoundError:
            raise HTTPException(status_code=404, detail="Job not found.")

    return router


router = create_jobs_router(job_service)
