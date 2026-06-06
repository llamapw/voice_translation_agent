<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

import JobStatus from "./components/JobStatus.vue";
import SubtitlePanel from "./components/SubtitlePanel.vue";
import UploadPanel from "./components/UploadPanel.vue";
import VideoPlayer from "./components/VideoPlayer.vue";
import {
  createJob as defaultCreateJob,
  getJob as defaultGetJob,
  type CreateJobInput,
} from "./api/jobs";
import {
  createJobEventSource as defaultCreateJobEventSource,
  parseJobEvent,
  type EventSourceFactory,
  type JobEvent,
} from "./api/jobEvents";
import { getSubtitles as defaultGetSubtitles } from "./api/subtitles";
import { isFinishedJob, type JobRead } from "./types/job";
import { formatCueTime, type SubtitleCue } from "./types/subtitle";

const props = withDefaults(
  defineProps<{
    createJob?: (input: CreateJobInput) => Promise<JobRead>;
    getJob?: (jobId: string) => Promise<JobRead>;
    getSubtitles?: (jobId: string) => Promise<SubtitleCue[]>;
    createJobEventSource?: (jobId: string, factory?: EventSourceFactory) => EventSource;
    pollIntervalMs?: number;
  }>(),
  {
    createJob: defaultCreateJob,
    getJob: defaultGetJob,
    getSubtitles: defaultGetSubtitles,
    createJobEventSource: defaultCreateJobEventSource,
    pollIntervalMs: 2000,
  },
);

const currentJob = ref<JobRead | null>(null);
const subtitles = ref<SubtitleCue[]>([]);
const liveSubtitle = ref<SubtitleCue | null>(null);
const videoPlayer = ref<{ seekTo: (seconds: number) => void } | null>(null);
const videoCurrentTime = ref(0);
const isSubmitting = ref(false);
const appError = ref<string | null>(null);
const eventStreamState = ref<"idle" | "open" | "closed">("idle");
let pollTimer: number | null = null;
let eventSource: EventSource | null = null;

const activeSubtitle = computed(
  () =>
    subtitles.value.find(
      (cue) => videoCurrentTime.value >= cue.start && videoCurrentTime.value <= cue.end,
    ) ?? null,
);
const displayedLiveSubtitle = computed(() => activeSubtitle.value ?? liveSubtitle.value);

function clearPollTimer(): void {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
}

function closeEventSource(): void {
  if (eventSource !== null) {
    eventSource.close();
    eventSource = null;
    eventStreamState.value = "closed";
  }
}

async function loadSubtitles(jobId: string): Promise<void> {
  try {
    const loadedSubtitles = await props.getSubtitles(jobId);
    subtitles.value = loadedSubtitles;
    liveSubtitle.value = loadedSubtitles[loadedSubtitles.length - 1] ?? null;
  } catch (error) {
    appError.value = error instanceof Error ? error.message : "字幕加载失败。";
  }
}

async function updateJob(job: JobRead): Promise<void> {
  currentJob.value = job;

  if (isFinishedJob(job)) {
    clearPollTimer();
  }

  if (job.status === "done") {
    if (subtitles.value.length === 0) {
      await loadSubtitles(job.id);
    }
  }
}

function appendSubtitle(cue: SubtitleCue): void {
  liveSubtitle.value = cue;
  const existingIndex = subtitles.value.findIndex((item) => item.index === cue.index);
  if (existingIndex >= 0) {
    subtitles.value.splice(existingIndex, 1, cue);
    return;
  }

  subtitles.value = [...subtitles.value, cue].sort((left, right) => left.index - right.index);
}

function handleVideoTimeUpdate(currentTime: number): void {
  videoCurrentTime.value = currentTime;
}

function handleSubtitleSelect(cue: SubtitleCue): void {
  videoPlayer.value?.seekTo(cue.start);
  videoCurrentTime.value = cue.start;
  liveSubtitle.value = cue;
}

function applyJobEvent(event: JobEvent): void {
  if (event.type === "subtitle_partial" && event.data.cue) {
    appendSubtitle(event.data.cue);
    return;
  }

  if (event.type === "job_status" && currentJob.value) {
    currentJob.value = {
      ...currentJob.value,
      status: event.data.status ?? currentJob.value.status,
      progress: event.data.progress ?? currentJob.value.progress,
      message: event.data.message ?? currentJob.value.message,
    };
    return;
  }

  if (event.type === "job_failed") {
    appError.value = event.data.error ?? "任务处理失败。";
    closeEventSource();
    clearPollTimer();
    return;
  }

  if (event.type === "job_done") {
    if (currentJob.value) {
      currentJob.value = {
        ...currentJob.value,
        status: "done",
        progress: 100,
        message: "Subtitle task completed.",
      };
    }
    clearPollTimer();
    return;
  }

  if (event.type === "job_closed") {
    closeEventSource();
  }
}

function addJobEventListener(source: EventSource, eventName: JobEvent["type"]): void {
  source.addEventListener(eventName, (message) => {
    applyJobEvent(parseJobEvent((message as MessageEvent).data));
  });
}

function startEventStream(jobId: string): void {
  closeEventSource();
  eventSource = props.createJobEventSource(jobId);
  eventStreamState.value = "open";
  for (const eventName of [
    "job_status",
    "subtitle_partial",
    "job_done",
    "job_failed",
    "job_closed",
  ] as const) {
    addJobEventListener(eventSource, eventName);
  }
  eventSource.onerror = () => {
    closeEventSource();
  };
}

async function pollJob(jobId: string): Promise<void> {
  try {
    await updateJob(await props.getJob(jobId));
  } catch (error) {
    clearPollTimer();
    appError.value = error instanceof Error ? error.message : "任务状态查询失败。";
  }
}

function startPolling(jobId: string): void {
  clearPollTimer();
  pollTimer = window.setInterval(() => {
    void pollJob(jobId);
  }, props.pollIntervalMs);
}

async function handleUpload(input: CreateJobInput): Promise<void> {
  isSubmitting.value = true;
  appError.value = null;
  eventStreamState.value = "idle";
  clearPollTimer();
  closeEventSource();

  try {
    subtitles.value = [];
    liveSubtitle.value = null;
    videoCurrentTime.value = 0;
    const job = await props.createJob(input);
    await updateJob(job);

    if (!isFinishedJob(job)) {
      startEventStream(job.id);
      startPolling(job.id);
    }
  } catch (error) {
    appError.value = error instanceof Error ? error.message : "任务创建失败。";
  } finally {
    isSubmitting.value = false;
  }
}

onBeforeUnmount(() => {
  clearPollTimer();
  closeEventSource();
});
</script>

<template>
  <main class="app-shell">
    <section class="app-workbench">
      <header class="app-topbar" data-testid="app-topbar">
        <div class="brand-block">
          <p class="eyebrow">Subtitle workflow</p>
          <h1>Voice Translation Agent</h1>
          <p class="summary">Upload, transcribe, translate, and export subtitles from one focused workspace.</p>
        </div>

        <div class="topbar-status">
          <span class="status-chip" :data-status="currentJob?.status ?? 'idle'">
            {{ currentJob?.status ?? "idle" }}
          </span>
          <p
            v-if="eventStreamState !== 'idle'"
            class="stream-state topbar-stream-state"
            :data-state="eventStreamState"
          >
            {{ eventStreamState === "open" ? "正在实时接收字幕" : "实时连接已关闭" }}
          </p>
        </div>
      </header>

      <p v-if="appError" class="error-message">{{ appError }}</p>

      <div class="workbench-layout">
        <aside class="control-rail" data-testid="control-rail">
          <UploadPanel :is-submitting="isSubmitting" @submit="handleUpload" />
        </aside>

        <section class="preview-stage" data-testid="preview-stage">
          <JobStatus :job="currentJob" />
          <VideoPlayer
            ref="videoPlayer"
            :video-url="currentJob?.video_url ?? null"
            :title="currentJob?.original_filename ?? null"
            @timeupdate="handleVideoTimeUpdate"
          />
          <section class="live-subtitle-panel" data-testid="live-subtitle">
            <div class="panel-heading">
              <h2>实时字幕</h2>
            </div>
            <div v-if="displayedLiveSubtitle" class="live-subtitle-body">
              <div class="live-subtitle-meta" data-testid="live-subtitle-meta">
                <span>当前 #{{ displayedLiveSubtitle.index }}</span>
                <span>
                  {{ formatCueTime(displayedLiveSubtitle.start) }} -
                  {{ formatCueTime(displayedLiveSubtitle.end) }}
                </span>
              </div>
              <p class="live-subtitle-source">{{ displayedLiveSubtitle.source_text }}</p>
              <p
                v-if="
                  displayedLiveSubtitle.target_text &&
                  displayedLiveSubtitle.target_text !== displayedLiveSubtitle.source_text
                "
                class="live-subtitle-target"
              >
                {{ displayedLiveSubtitle.target_text }}
              </p>
            </div>
            <div v-else class="empty-state">
              等待实时字幕
            </div>
          </section>
        </section>

        <aside class="subtitle-rail" data-testid="subtitle-rail">
          <SubtitlePanel
            :cues="subtitles"
            :srt-url="currentJob?.srt_download_url ?? null"
            :active-cue-index="activeSubtitle?.index ?? null"
            @select="handleSubtitleSelect"
          />
        </aside>
      </div>
    </section>
  </main>
</template>
