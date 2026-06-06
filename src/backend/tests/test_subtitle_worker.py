from app.core.paths import build_job_paths
from app.models.job import JobCreateOptions, JobStatus
from app.models.job_event import JobEventType
from app.models.subtitle import SubtitleCue
from app.services.job_event_service import JobEventService
from app.services.job_service import JobService
from app.services.subtitle_service import SubtitleService
from app.workers.subtitle_worker import run_mock_subtitle_job, run_subtitle_job


class FakeMediaService:
    def __init__(self):
        self.calls = []

    def extract_audio(self, input_video, output_audio):
        self.calls.append((input_video, output_audio))
        output_audio.write_bytes(b"fake audio")
        return output_audio


class FakeASRService:
    def __init__(self):
        self.calls = []

    def transcribe(self, audio_path):
        self.calls.append(audio_path)
        return [
            SubtitleCue(
                index=1,
                start=0.0,
                end=2.0,
                source_text="helo world",
                target_text="helo world",
            )
        ]


class FakeLLMService:
    def __init__(self):
        self.calls = []

    def enrich_subtitles(self, cues, correct, target_language, subtitle_mode, on_cue=None):
        self.calls.append((cues, correct, target_language, subtitle_mode, on_cue))
        enriched = [
            SubtitleCue(
                index=1,
                start=0.0,
                end=2.0,
                source_text="Hello, world.",
                target_text="你好，世界。",
            )
        ]
        if on_cue is not None:
            for cue in enriched:
                on_cue(cue)
        return enriched


class FailingMediaService:
    def extract_audio(self, input_video, output_audio):
        raise RuntimeError("ffmpeg failed")


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


def test_run_mock_subtitle_job_publishes_sse_events(tmp_path):
    job_service = JobService()
    subtitle_service = SubtitleService()
    event_service = JobEventService()
    job = job_service.create_job(options=JobCreateOptions(), original_filename="input.mp4")
    paths = build_job_paths(job.id, storage_root=tmp_path)

    run_mock_subtitle_job(
        job_id=job.id,
        paths=paths,
        job_service=job_service,
        subtitle_service=subtitle_service,
        event_service=event_service,
    )

    events = []
    while True:
        event = event_service.next_event(job.id, timeout=0.01)
        if event is None:
            break
        events.append(event)
        if event.type == JobEventType.job_closed:
            break

    assert [event.type for event in events] == [
        JobEventType.job_status,
        JobEventType.job_status,
        JobEventType.job_status,
        JobEventType.subtitle_partial,
        JobEventType.job_done,
        JobEventType.job_closed,
    ]
    assert events[3].data["cue"]["source_text"] == "Sample source subtitle."


def test_run_subtitle_job_processes_video_with_injected_services(tmp_path):
    job_service = JobService()
    subtitle_service = SubtitleService()
    media_service = FakeMediaService()
    asr_service = FakeASRService()
    llm_service = FakeLLMService()
    job = job_service.create_job(
        options=JobCreateOptions(
            target_language="zh",
            correct=True,
            subtitle_mode="bilingual",
        ),
        original_filename="input.mp4",
    )
    paths = build_job_paths(job.id, storage_root=tmp_path)
    paths.input_video.parent.mkdir(parents=True, exist_ok=True)
    paths.input_video.write_bytes(b"fake video")

    result = run_subtitle_job(
        job_id=job.id,
        paths=paths,
        job_service=job_service,
        media_service=media_service,
        asr_service=asr_service,
        llm_service=llm_service,
        subtitle_service=subtitle_service,
    )

    updated = job_service.get_job(job.id)
    assert result.status == JobStatus.done
    assert updated.status == JobStatus.done
    assert updated.progress == 100
    assert media_service.calls == [(paths.input_video, paths.audio_wav)]
    assert asr_service.calls == [paths.audio_wav]
    assert llm_service.calls[0][1:4] == (True, "zh", "bilingual")
    assert paths.audio_wav.read_bytes() == b"fake audio"
    assert paths.subtitles_json.exists()
    assert paths.output_srt.exists()
    assert "Hello, world." in paths.output_srt.read_text(encoding="utf-8")
    assert "你好，世界。" in paths.output_srt.read_text(encoding="utf-8")


def test_run_subtitle_job_publishes_events_for_real_worker(tmp_path):
    job_service = JobService()
    subtitle_service = SubtitleService()
    media_service = FakeMediaService()
    asr_service = FakeASRService()
    llm_service = FakeLLMService()
    event_service = JobEventService()
    job = job_service.create_job(
        options=JobCreateOptions(
            target_language="zh",
            correct=True,
            subtitle_mode="bilingual",
        ),
        original_filename="input.mp4",
    )
    paths = build_job_paths(job.id, storage_root=tmp_path)
    paths.input_video.parent.mkdir(parents=True, exist_ok=True)
    paths.input_video.write_bytes(b"fake video")

    run_subtitle_job(
        job_id=job.id,
        paths=paths,
        job_service=job_service,
        media_service=media_service,
        asr_service=asr_service,
        llm_service=llm_service,
        subtitle_service=subtitle_service,
        event_service=event_service,
    )

    events = []
    while True:
        event = event_service.next_event(job.id, timeout=0.01)
        if event is None:
            break
        events.append(event)
        if event.type == JobEventType.job_closed:
            break

    event_types = [event.type for event in events]
    assert JobEventType.subtitle_partial in event_types
    assert JobEventType.job_done in event_types
    assert event_types[-1] == JobEventType.job_closed


def test_run_subtitle_job_marks_job_failed_when_processing_raises(tmp_path):
    job_service = JobService()
    subtitle_service = SubtitleService()
    job = job_service.create_job(options=JobCreateOptions(), original_filename="input.mp4")
    paths = build_job_paths(job.id, storage_root=tmp_path)
    paths.input_video.parent.mkdir(parents=True, exist_ok=True)
    paths.input_video.write_bytes(b"fake video")

    result = run_subtitle_job(
        job_id=job.id,
        paths=paths,
        job_service=job_service,
        media_service=FailingMediaService(),
        asr_service=FakeASRService(),
        llm_service=FakeLLMService(),
        subtitle_service=subtitle_service,
    )

    updated = job_service.get_job(job.id)
    assert result.status == JobStatus.failed
    assert updated.status == JobStatus.failed
    assert updated.error == "ffmpeg failed"
