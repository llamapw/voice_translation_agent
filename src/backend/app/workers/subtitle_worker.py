from app.core.paths import JobPaths
from app.models.job import JobRead, JobStatus
from app.models.subtitle import SubtitleCue
from app.services.job_service import JobService
from app.services.subtitle_service import SubtitleService


def run_mock_subtitle_job(
    job_id: str,
    paths: JobPaths,
    job_service: JobService,
    subtitle_service: SubtitleService,
) -> JobRead:
    job_service.update_job(
        job_id,
        status=JobStatus.extracting_audio,
        progress=20,
        message="Extracting audio from video.",
    )
    job_service.update_job(
        job_id,
        status=JobStatus.transcribing,
        progress=50,
        message="Transcribing speech.",
    )
    job_service.update_job(
        job_id,
        status=JobStatus.generating_subtitle,
        progress=90,
        message="Generating subtitle files.",
    )

    cues = [
        SubtitleCue(
            index=1,
            start=0.0,
            end=3.0,
            source_text="Sample source subtitle.",
            target_text="示例目标字幕。",
        )
    ]
    subtitle_service.write_subtitles_json(cues, paths.subtitles_json)
    subtitle_service.write_srt(cues, paths.output_srt)

    return job_service.update_job(
        job_id,
        status=JobStatus.done,
        progress=100,
        message="Subtitle task completed.",
    )
