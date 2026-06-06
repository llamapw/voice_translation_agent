<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";

import JobStatus from "./components/JobStatus.vue";
import SubtitlePanel from "./components/SubtitlePanel.vue";
import UploadPanel from "./components/UploadPanel.vue";
import VideoPlayer from "./components/VideoPlayer.vue";
import {
  createJob as defaultCreateJob,
  getJob as defaultGetJob,
  type CreateJobInput,
} from "./api/jobs";
import { getSubtitles as defaultGetSubtitles } from "./api/subtitles";
import { isFinishedJob, type JobRead } from "./types/job";
import type { SubtitleCue } from "./types/subtitle";

const props = withDefaults(
  defineProps<{
    createJob?: (input: CreateJobInput) => Promise<JobRead>;
    getJob?: (jobId: string) => Promise<JobRead>;
    getSubtitles?: (jobId: string) => Promise<SubtitleCue[]>;
    pollIntervalMs?: number;
  }>(),
  {
    createJob: defaultCreateJob,
    getJob: defaultGetJob,
    getSubtitles: defaultGetSubtitles,
    pollIntervalMs: 2000,
  },
);

const currentJob = ref<JobRead | null>(null);
const subtitles = ref<SubtitleCue[]>([]);
const isSubmitting = ref(false);
const appError = ref<string | null>(null);
let pollTimer: number | null = null;

function clearPollTimer(): void {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function loadSubtitles(jobId: string): Promise<void> {
  try {
    subtitles.value = await props.getSubtitles(jobId);
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
    await loadSubtitles(job.id);
  }
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
  clearPollTimer();

  try {
    subtitles.value = [];
    const job = await props.createJob(input);
    await updateJob(job);

    if (!isFinishedJob(job)) {
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
});
</script>

<template>
  <main class="app-shell">
    <section class="workspace">
      <header class="workspace-header">
        <p class="eyebrow">Subtitle workflow</p>
        <h1>Voice Translation Agent</h1>
        <p class="summary">Upload, transcribe, translate, and export subtitles from one focused workspace.</p>
      </header>

      <div class="workspace-grid">
        <div class="control-column">
          <UploadPanel :is-submitting="isSubmitting" @submit="handleUpload" />
          <p v-if="appError" class="error-message">{{ appError }}</p>
        </div>

        <div class="result-column">
          <JobStatus :job="currentJob" />
          <VideoPlayer
            :video-url="currentJob?.video_url ?? null"
            :title="currentJob?.original_filename ?? null"
          />
          <SubtitlePanel
            :cues="subtitles"
            :srt-url="currentJob?.srt_download_url ?? null"
          />
        </div>
      </div>
    </section>
  </main>
</template>
