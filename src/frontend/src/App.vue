<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";

import JobStatus from "./components/JobStatus.vue";
import UploadPanel from "./components/UploadPanel.vue";
import {
  createJob as defaultCreateJob,
  getJob as defaultGetJob,
  type CreateJobInput,
} from "./api/jobs";
import { isFinishedJob, type JobRead } from "./types/job";

const props = withDefaults(
  defineProps<{
    createJob?: (input: CreateJobInput) => Promise<JobRead>;
    getJob?: (jobId: string) => Promise<JobRead>;
    pollIntervalMs?: number;
  }>(),
  {
    createJob: defaultCreateJob,
    getJob: defaultGetJob,
    pollIntervalMs: 2000,
  },
);

const currentJob = ref<JobRead | null>(null);
const isSubmitting = ref(false);
const appError = ref<string | null>(null);
let pollTimer: number | null = null;

function clearPollTimer(): void {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
}

function updateJob(job: JobRead): void {
  currentJob.value = job;

  if (isFinishedJob(job)) {
    clearPollTimer();
  }
}

async function pollJob(jobId: string): Promise<void> {
  try {
    updateJob(await props.getJob(jobId));
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
    const job = await props.createJob(input);
    updateJob(job);

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

        <JobStatus :job="currentJob" />
      </div>
    </section>
  </main>
</template>
