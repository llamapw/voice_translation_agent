from concurrent.futures import Future, ThreadPoolExecutor, wait
from threading import Lock
from typing import Dict, List, Optional

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
    translation_executor: Optional[ThreadPoolExecutor] = None
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
        use_audio_stream = hasattr(media_service, "stream_audio") and hasattr(
            asr_service,
            "transcribe_wav_stream",
        )
        audio_input = (
            media_service.stream_audio(paths.input_video, paths.audio_wav)
            if use_audio_stream
            else media_service.extract_audio(paths.input_video, paths.audio_wav)
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
        job = job_service.get_job(job_id)
        correct = job.correct
        source_language = job.source_language
        target_language = job.target_language
        subtitle_mode = job.subtitle_mode
        realtime_enriched_cues: Dict[int, SubtitleCue] = {}
        translation_futures: List[Future] = []
        translation_lock = Lock()
        if event_service is not None:
            translation_executor = ThreadPoolExecutor(max_workers=2)

        def enrich_and_publish_cue(cue: SubtitleCue) -> Optional[SubtitleCue]:
            enriched = llm_service.enrich_subtitles(
                [cue],
                correct=correct,
                source_language=source_language,
                target_language=target_language,
                subtitle_mode=subtitle_mode,
            )
            if not enriched:
                return None
            enriched_cue = enriched[0]
            with translation_lock:
                realtime_enriched_cues[enriched_cue.index] = enriched_cue
            if event_service is not None:
                event_service.publish(
                    JobEvent.subtitle_partial(job_id=job_id, cue=enriched_cue)
                )
            return enriched_cue

        def publish_enriched_cue(cue: SubtitleCue) -> None:
            if event_service is None:
                return
            event_service.publish(JobEvent.subtitle_partial(job_id=job_id, cue=cue))
            if translation_executor is not None:
                translation_futures.append(
                    translation_executor.submit(enrich_and_publish_cue, cue)
                )

        def wait_for_realtime_enrichment() -> Dict[int, SubtitleCue]:
            if not translation_futures:
                return {}
            wait(translation_futures)
            for future in translation_futures:
                future.result()
            with translation_lock:
                return dict(realtime_enriched_cues)

        if use_audio_stream:
            cues = asr_service.transcribe_wav_stream(
                audio_input,
                on_cue=publish_enriched_cue if event_service is not None else None,
            )
        else:
            cues = asr_service.transcribe(
                audio_input,
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
        realtime_enriched_by_index = wait_for_realtime_enrichment()
        missing_cues = [
            cue for cue in cues if cue.index not in realtime_enriched_by_index
        ]
        fallback_enriched_by_index: Dict[int, SubtitleCue] = {}
        if missing_cues:
            fallback_enriched_by_index = {
                cue.index: cue
                for cue in llm_service.enrich_subtitles(
                    missing_cues,
                    correct=job.correct,
                    source_language=job.source_language,
                    target_language=job.target_language,
                    subtitle_mode=job.subtitle_mode,
                )
            }
        enriched_cues = [
            realtime_enriched_by_index.get(cue.index)
            or fallback_enriched_by_index.get(cue.index)
            or cue
            for cue in cues
        ]

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
    finally:
        if translation_executor is not None:
            translation_executor.shutdown(wait=True)


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
