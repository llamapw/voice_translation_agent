from typing import Optional

from app.core.paths import JobPaths
from app.models.job import JobRead, JobStatus
from app.models.job_event import JobEvent
from app.models.subtitle import SubtitleCue
from app.services.asr_service import ASRService
from app.services.job_event_service import JobEventService
from app.services.job_service import JobService
from app.services.llm_service import LLMService
from app.services.media_service import MediaService
from app.services.subtitle_service import SubtitleService


def run_subtitle_job(
    job_id: str,
    paths: JobPaths,
    job_service: JobService,
    media_service: MediaService,
    asr_service: ASRService,
    llm_service: LLMService,
    subtitle_service: SubtitleService,
    event_service: Optional[JobEventService] = None,
) -> JobRead:
    try:
        job_service.update_job(
            job_id,
            status=JobStatus.extracting_audio,
            progress=20,
            message="Extracting audio from video.",
        )
        if event_service is not None:
            event_service.publish(
                JobEvent.status(
                    job_id=job_id,
                    status=JobStatus.extracting_audio.value,
                    progress=20,
                    message="Extracting audio from video.",
                )
            )
        media_service.extract_audio(paths.input_video, paths.audio_wav)

        job_service.update_job(
            job_id,
            status=JobStatus.transcribing,
            progress=50,
            message="Transcribing speech.",
        )
        if event_service is not None:
            event_service.publish(
                JobEvent.status(
                    job_id=job_id,
                    status=JobStatus.transcribing.value,
                    progress=50,
                    message="Transcribing speech.",
                )
        )
        job = job_service.get_job(job_id)

        def publish_enriched_cue(cue: SubtitleCue) -> None:
            if event_service is None:
                return
            enriched = llm_service.enrich_subtitles(
                [cue],
                correct=job.correct,
                source_language=job.source_language,
                target_language=job.target_language,
                subtitle_mode=job.subtitle_mode,
            )
            if enriched:
                event_service.publish(
                    JobEvent.subtitle_partial(job_id=job_id, cue=enriched[0])
                )

        cues = asr_service.transcribe(
            paths.audio_wav,
            on_cue=publish_enriched_cue if event_service is not None else None,
        )

        job = job_service.update_job(
            job_id,
            status=JobStatus.correcting,
            progress=75,
            message="Correcting and translating subtitles.",
        )
        if event_service is not None:
            event_service.publish(
                JobEvent.status(
                    job_id=job_id,
                    status=JobStatus.correcting.value,
                    progress=75,
                    message="Correcting and translating subtitles.",
                )
            )
        enriched_cues = llm_service.enrich_subtitles(
            cues,
            correct=job.correct,
            source_language=job.source_language,
            target_language=job.target_language,
            subtitle_mode=job.subtitle_mode,
        )

        job_service.update_job(
            job_id,
            status=JobStatus.generating_subtitle,
            progress=90,
            message="Generating subtitle files.",
        )
        if event_service is not None:
            event_service.publish(
                JobEvent.status(
                    job_id=job_id,
                    status=JobStatus.generating_subtitle.value,
                    progress=90,
                    message="Generating subtitle files.",
                )
            )
        subtitle_service.write_subtitles_json(enriched_cues, paths.subtitles_json)
        subtitle_service.write_srt(enriched_cues, paths.output_srt)

        result = job_service.update_job(
            job_id,
            status=JobStatus.done,
            progress=100,
            message="Subtitle task completed.",
        )
        if event_service is not None:
            event_service.publish(JobEvent.done(job_id=job_id))
            event_service.close(job_id)
        return result
    except Exception as error:
        result = job_service.fail_job(job_id, str(error))
        if event_service is not None:
            event_service.publish(JobEvent.failed(job_id=job_id, error=str(error)))
            event_service.close(job_id)
        return result


def run_mock_subtitle_job(
    job_id: str,
    paths: JobPaths,
    job_service: JobService,
    subtitle_service: SubtitleService,
    event_service: Optional[JobEventService] = None,
) -> JobRead:
    job_service.update_job(
        job_id,
        status=JobStatus.extracting_audio,
        progress=20,
        message="Extracting audio from video.",
    )
    if event_service is not None:
        event_service.publish(
            JobEvent.status(
                job_id=job_id,
                status=JobStatus.extracting_audio.value,
                progress=20,
                message="Extracting audio from video.",
            )
        )
    job_service.update_job(
        job_id,
        status=JobStatus.transcribing,
        progress=50,
        message="Transcribing speech.",
    )
    if event_service is not None:
        event_service.publish(
            JobEvent.status(
                job_id=job_id,
                status=JobStatus.transcribing.value,
                progress=50,
                message="Transcribing speech.",
            )
        )
    job_service.update_job(
        job_id,
        status=JobStatus.generating_subtitle,
        progress=90,
        message="Generating subtitle files.",
    )
    if event_service is not None:
        event_service.publish(
            JobEvent.status(
                job_id=job_id,
                status=JobStatus.generating_subtitle.value,
                progress=90,
                message="Generating subtitle files.",
            )
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
    if event_service is not None:
        for cue in cues:
            event_service.publish(JobEvent.subtitle_partial(job_id=job_id, cue=cue))
    subtitle_service.write_subtitles_json(cues, paths.subtitles_json)
    subtitle_service.write_srt(cues, paths.output_srt)

    result = job_service.update_job(
        job_id,
        status=JobStatus.done,
        progress=100,
        message="Subtitle task completed.",
    )
    if event_service is not None:
        event_service.publish(JobEvent.done(job_id=job_id))
        event_service.close(job_id)
    return result
