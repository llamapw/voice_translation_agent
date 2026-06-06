<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

import InsightPanel from "./components/InsightPanel.vue";
import JobStatus from "./components/JobStatus.vue";
import SubtitlePanel from "./components/SubtitlePanel.vue";
import UploadPanel from "./components/UploadPanel.vue";
import VideoPlayer from "./components/VideoPlayer.vue";
import { generateInsight as defaultGenerateInsight } from "./api/insights";
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
import type { InsightItem, InsightRead } from "./types/insight";
import { isFinishedJob, statusLabel, type JobRead } from "./types/job";
import { formatCueTime, type SubtitleCue } from "./types/subtitle";
import { buildInsightTermNames } from "./utils/termHighlight";

const props = withDefaults(
  defineProps<{
    createJob?: (input: CreateJobInput) => Promise<JobRead>;
    getJob?: (jobId: string) => Promise<JobRead>;
    getSubtitles?: (jobId: string) => Promise<SubtitleCue[]>;
    generateInsight?: (jobId: string) => Promise<InsightRead>;
    createJobEventSource?: (jobId: string, factory?: EventSourceFactory) => EventSource;
    pollIntervalMs?: number;
  }>(),
  {
    createJob: defaultCreateJob,
    getJob: defaultGetJob,
    getSubtitles: defaultGetSubtitles,
    generateInsight: defaultGenerateInsight,
    createJobEventSource: defaultCreateJobEventSource,
    pollIntervalMs: 2000,
  },
);

const currentJob = ref<JobRead | null>(null);
const subtitles = ref<SubtitleCue[]>([]);
const insight = ref<InsightRead | null>(null);
const liveSubtitle = ref<SubtitleCue | null>(null);
const videoPlayer = ref<{ seekTo: (seconds: number) => void } | null>(null);
const videoCurrentTime = ref(0);
const isSubmitting = ref(false);
const isGeneratingInsight = ref(false);
const appError = ref<string | null>(null);
const eventStreamState = ref<"idle" | "open" | "closed">("idle");
const activeResultTab = ref<"subtitles" | "insight">("subtitles");
const isResultRailCollapsed = ref(false);
const resultRailWidth = ref(430);
let pollTimer: number | null = null;
let eventSource: EventSource | null = null;

const activeSubtitle = computed(
  () =>
    subtitles.value.find(
      (cue) => videoCurrentTime.value >= cue.start && videoCurrentTime.value <= cue.end,
    ) ?? null,
);
const activeInsightItem = computed(
  () =>
    insight.value?.items.find(
      (item) => videoCurrentTime.value >= item.start && videoCurrentTime.value <= item.end,
    ) ?? null,
);
const displayedLiveSubtitle = computed(() => activeSubtitle.value ?? liveSubtitle.value);
const displayedLiveSubtitleText = computed(() => {
  const cue = displayedLiveSubtitle.value;
  const subtitleMode = currentJob.value?.subtitle_mode ?? "bilingual";

  if (!cue) {
    return null;
  }

  if (subtitleMode === "target") {
    const hasTranslatedText = cue.target_text && cue.target_text !== cue.source_text;

    return {
      primary: hasTranslatedText ? cue.target_text : "正在翻译...",
      secondary: null,
    };
  }

  if (subtitleMode === "source") {
    return {
      primary: cue.source_text,
      secondary: null,
    };
  }

  return {
    primary: cue.source_text,
    secondary:
      cue.target_text && cue.target_text !== cue.source_text ? cue.target_text : null,
  };
});
const topbarStatusLabel = computed(() =>
  currentJob.value ? statusLabel[currentJob.value.status] : "等待任务",
);
const topbarProgressLabel = computed(() => `${currentJob.value?.progress ?? 0}%`);
const topbarSubtitleCountLabel = computed(() => `${subtitles.value.length} 条字幕`);
const canGenerateInsight = computed(() => currentJob.value?.status === "done");
const glossaryTerms = computed(() => buildInsightTermNames(insight.value?.items ?? []));
const workbenchLayoutStyle = computed(() => ({
  "--result-rail-width": isResultRailCollapsed.value ? "56px" : `${resultRailWidth.value}px`,
}));

function clampResultRailWidth(width: number): number {
  return Math.min(620, Math.max(360, width));
}

function setResultRailCollapsed(collapsed: boolean): void {
  isResultRailCollapsed.value = collapsed;
}

function handleResultRailResize(event: PointerEvent): void {
  if (isResultRailCollapsed.value) {
    return;
  }

  const workbench = document.querySelector(".app-workbench");
  const rightEdge =
    workbench instanceof HTMLElement ? workbench.getBoundingClientRect().right : window.innerWidth;
  const nextWidth = rightEdge - event.clientX;
  resultRailWidth.value = clampResultRailWidth(nextWidth);
}

function stopResultRailResize(): void {
  window.removeEventListener("pointermove", handleResultRailResize);
  window.removeEventListener("pointerup", stopResultRailResize);
}

function startResultRailResize(event: PointerEvent): void {
  if (isResultRailCollapsed.value) {
    return;
  }

  event.preventDefault();
  window.addEventListener("pointermove", handleResultRailResize);
  window.addEventListener("pointerup", stopResultRailResize);
}

function handleResultRailResizeKeydown(event: KeyboardEvent): void {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
    return;
  }

  event.preventDefault();
  const delta = event.key === "ArrowLeft" ? 24 : -24;
  resultRailWidth.value = clampResultRailWidth(resultRailWidth.value + delta);
}

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

function handleInsightSelect(item: InsightItem): void {
  videoPlayer.value?.seekTo(item.start);
  videoCurrentTime.value = item.start;
}

async function handleGenerateInsight(): Promise<void> {
  if (!currentJob.value) {
    return;
  }

  isGeneratingInsight.value = true;
  appError.value = null;

  try {
    insight.value = await props.generateInsight(currentJob.value.id);
  } catch (error) {
    appError.value = error instanceof Error ? error.message : "知识笔记生成失败。";
  } finally {
    isGeneratingInsight.value = false;
  }
}

async function applyJobEvent(event: JobEvent): Promise<void> {
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
    const errorMessage = event.data.error ?? "任务处理失败。";
    appError.value = errorMessage;
    if (currentJob.value) {
      currentJob.value = {
        ...currentJob.value,
        status: "failed",
        progress: 100,
        message: "Task failed.",
        error: errorMessage,
      };
    }
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
      if (subtitles.value.length === 0) {
        await loadSubtitles(currentJob.value.id);
      }
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
    void applyJobEvent(parseJobEvent((message as MessageEvent).data));
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
    insight.value = null;
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
  stopResultRailResize();
});
</script>

<template>
  <main class="app-shell">
    <section class="app-workbench">
      <header class="app-topbar" data-testid="app-topbar">
        <div class="brand-block">
          <p class="eyebrow">Voice Translation Agent</p>
          <h1>实时字幕工作台</h1>
          <p class="summary">上传视频、同步字幕、沉淀知识笔记，在一个界面里完成从听懂到复盘。</p>
        </div>

        <ol class="workflow-steps" data-testid="workflow-steps" aria-label="工作流阶段">
          <li>
            <span>01</span>
            <strong>导入</strong>
          </li>
          <li>
            <span>02</span>
            <strong>转写翻译</strong>
          </li>
          <li>
            <span>03</span>
            <strong>知识整理</strong>
          </li>
        </ol>

        <div class="topbar-status">
          <div class="topbar-metric">
            <span>状态</span>
            <strong class="status-chip" :data-status="currentJob?.status ?? 'idle'">
              {{ topbarStatusLabel }}
            </strong>
          </div>
          <div class="topbar-metric">
            <span>进度</span>
            <strong>{{ topbarProgressLabel }}</strong>
          </div>
          <div class="topbar-metric">
            <span>字幕</span>
            <strong>{{ topbarSubtitleCountLabel }}</strong>
          </div>
          <p
            v-if="eventStreamState !== 'idle'"
            class="stream-state topbar-stream-state"
            :data-state="eventStreamState"
          >
            {{ eventStreamState === "open" ? "正在实时接收字幕" : "实时连接已关闭" }}
          </p>
        </div>
      </header>

      <p v-if="appError" class="error-message" role="alert">{{ appError }}</p>

      <div
        class="workbench-layout"
        :data-result-rail-collapsed="isResultRailCollapsed"
        :style="workbenchLayoutStyle"
      >
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
              <p class="live-subtitle-source">{{ displayedLiveSubtitleText?.primary }}</p>
              <p
                v-if="displayedLiveSubtitleText?.secondary"
                class="live-subtitle-target"
              >
                {{ displayedLiveSubtitleText.secondary }}
              </p>
            </div>
            <div v-else class="empty-state">
              等待实时字幕
            </div>
          </section>
        </section>

        <aside
          class="subtitle-rail"
          data-testid="subtitle-rail"
          :data-collapsed="isResultRailCollapsed"
        >
          <button
            v-if="isResultRailCollapsed"
            class="result-rail-expand"
            data-testid="result-rail-expand"
            type="button"
            aria-label="展开结果边栏"
            @click="setResultRailCollapsed(false)"
          >
            结果
            <span>{{ subtitles.length }}</span>
          </button>

          <div
            v-if="!isResultRailCollapsed"
            class="result-resize-handle"
            data-testid="result-resize-handle"
            role="separator"
            aria-label="调整结果边栏宽度"
            aria-orientation="vertical"
            tabindex="0"
            @pointerdown="startResultRailResize"
            @keydown="handleResultRailResizeKeydown"
          />

          <section v-if="!isResultRailCollapsed" class="result-workspace">
            <div class="result-rail-header">
              <div>
                <span>结果边栏</span>
                <strong>{{ activeResultTab === "subtitles" ? "字幕时间轴" : "知识笔记" }}</strong>
              </div>
              <button
                class="result-rail-toggle"
                data-testid="result-rail-collapse"
                type="button"
                aria-label="收起结果边栏"
                @click="setResultRailCollapsed(true)"
              >
                收起
              </button>
            </div>

            <div class="result-tabs" data-testid="result-tabs" role="tablist" aria-label="结果视图">
              <button
                data-testid="result-tab-subtitles"
                type="button"
                role="tab"
                :aria-selected="activeResultTab === 'subtitles'"
                :data-active="activeResultTab === 'subtitles'"
                @click="activeResultTab = 'subtitles'"
              >
                字幕
                <span>{{ subtitles.length }}</span>
              </button>
              <button
                data-testid="result-tab-insight"
                type="button"
                role="tab"
                :aria-selected="activeResultTab === 'insight'"
                :data-active="activeResultTab === 'insight'"
                @click="activeResultTab = 'insight'"
              >
                笔记
                <span>{{ insight?.items.length ?? 0 }}</span>
              </button>
            </div>

            <div class="result-pane">
              <SubtitlePanel
                v-if="activeResultTab === 'subtitles'"
                data-testid="subtitle-panel"
                :cues="subtitles"
                :srt-url="currentJob?.srt_download_url ?? null"
                :active-cue-index="activeSubtitle?.index ?? null"
                :terms="glossaryTerms"
                @select="handleSubtitleSelect"
              />
              <InsightPanel
                v-else
                data-testid="insight-panel"
                :insight="insight"
                :is-loading="isGeneratingInsight"
                :can-generate="canGenerateInsight"
                :active-item-id="activeInsightItem?.id ?? null"
                @generate="handleGenerateInsight"
                @select-item="handleInsightSelect"
              />
            </div>
          </section>
        </aside>
      </div>
    </section>
  </main>
</template>
