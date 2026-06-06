import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App.vue";
import type { JobEvent } from "./api/jobEvents";
import type { InsightRead } from "./types/insight";
import type { JobRead } from "./types/job";
import type { SubtitleCue } from "./types/subtitle";

const subtitles: SubtitleCue[] = [
  {
    index: 1,
    start: 0.55,
    end: 13.51,
    source_text: "Hello",
    target_text: "你好",
    display_text: "Hello\n你好",
  },
];

const timelineSubtitles: SubtitleCue[] = [
  subtitles[0],
  {
    index: 2,
    start: 14,
    end: 18.5,
    source_text: "Next line",
    target_text: "下一句",
    display_text: "Next line\n下一句",
  },
];

const insight: InsightRead = {
  job_id: "job_test",
  summary: "运动会产生热量。汗液帮助身体降温。",
  items: [
    {
      id: "key_point_1",
      type: "key_point",
      title: "运动产生热量",
      content: "运动时大部分能量会转化为热量。",
      start: 0.55,
      end: 13.51,
      source_cue_indexes: [1],
    },
  ],
  markdown_url: "/api/jobs/job_test/insights/markdown",
};

const insightWithTerm: InsightRead = {
  ...insight,
  items: [
    ...insight.items,
    {
      id: "term_1",
      type: "term",
      title: "热应激",
      content: "身体热量压力相关概念。",
      source_term: "heat stress",
      target_term: "热应激",
      start: 0.55,
      end: 13.51,
      source_cue_indexes: [1],
    },
  ],
};

function buildJob(overrides: Partial<JobRead> = {}): JobRead {
  return {
    id: "job_test",
    status: "pending",
    progress: 0,
    message: "Task is waiting to start.",
    source_language: "zh",
    target_language: "zh",
    correct: true,
    asr_model: "paraformer-v2",
    llm_model: "default",
    subtitle_mode: "bilingual",
    original_filename: "demo.mp4",
    input_extension: ".mp4",
    video_url: "/api/jobs/job_test/video",
    subtitle_url: "/api/jobs/job_test/subtitles",
    srt_download_url: "/api/jobs/job_test/srt",
    error: null,
    ...overrides,
  };
}

class FakeEventSource {
  readonly listeners: Record<string, Array<(event: MessageEvent) => void>> = {};
  closed = false;

  addEventListener(type: string, listener: EventListener): void {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(listener as (event: MessageEvent) => void);
  }

  close(): void {
    this.closed = true;
  }

  emit(event: JobEvent): void {
    for (const listener of this.listeners[event.type] ?? []) {
      listener(new MessageEvent(event.type, { data: JSON.stringify(event) }));
    }
  }
}

describe("App", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the frontend shell", () => {
    const wrapper = mount(App);

    expect(wrapper.text()).toContain("Voice Translation Agent");
  });

  it("renders the workbench layout regions", () => {
    const wrapper = mount(App);

    expect(wrapper.find('[data-testid="app-topbar"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="workflow-steps"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="control-rail"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="preview-stage"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="subtitle-rail"]').exists()).toBe(true);
  });

  it("renders the redesigned workbench identity and workflow stages", () => {
    const wrapper = mount(App);
    const topbar = wrapper.get('[data-testid="app-topbar"]');
    const workflowSteps = wrapper.get('[data-testid="workflow-steps"]');

    expect(topbar.text()).toContain("实时字幕工作台");
    expect(topbar.text()).toContain("上传视频、同步字幕、沉淀知识笔记");
    expect(workflowSteps.text()).toContain("导入");
    expect(workflowSteps.text()).toContain("转写翻译");
    expect(workflowSteps.text()).toContain("知识整理");
  });

  it("switches the result rail between subtitles and notes", async () => {
    const wrapper = mount(App);

    expect(wrapper.get('[data-testid="result-tabs"]').text()).toContain("字幕");
    expect(wrapper.get('[data-testid="subtitle-panel"]').isVisible()).toBe(true);
    expect(wrapper.find('[data-testid="insight-panel"]').exists()).toBe(false);

    await wrapper.get('[data-testid="result-tab-insight"]').trigger("click");

    expect(wrapper.get('[data-testid="insight-panel"]').isVisible()).toBe(true);
    expect(wrapper.find('[data-testid="subtitle-panel"]').exists()).toBe(false);
  });

  it("collapses and expands the result rail", async () => {
    const wrapper = mount(App);

    expect(wrapper.get('[data-testid="subtitle-rail"]').attributes("data-collapsed")).toBe(
      "false",
    );

    await wrapper.get('[data-testid="result-rail-collapse"]').trigger("click");

    expect(wrapper.get('[data-testid="subtitle-rail"]').attributes("data-collapsed")).toBe("true");
    expect(wrapper.find('[data-testid="result-tabs"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="result-rail-expand"]').text()).toContain("结果");

    await wrapper.get('[data-testid="result-rail-expand"]').trigger("click");

    expect(wrapper.get('[data-testid="subtitle-rail"]').attributes("data-collapsed")).toBe(
      "false",
    );
    expect(wrapper.find('[data-testid="result-tabs"]').exists()).toBe(true);
  });

  it("resizes the result rail with keyboard controls", async () => {
    const wrapper = mount(App);
    const layout = wrapper.get(".workbench-layout");

    expect(layout.attributes("style")).toContain("--result-rail-width: 430px");

    await wrapper.get('[data-testid="result-resize-handle"]').trigger("keydown", {
      key: "ArrowLeft",
    });

    expect(layout.attributes("style")).toContain("--result-rail-width: 454px");

    await wrapper.get('[data-testid="result-resize-handle"]').trigger("keydown", {
      key: "ArrowRight",
    });

    expect(layout.attributes("style")).toContain("--result-rail-width: 430px");
  });

  it("renders localized topbar status metrics after a job is loaded", async () => {
    vi.useFakeTimers();
    const createdJob = buildJob();
    const doneJob = buildJob({
      status: "done",
      progress: 100,
      message: "Subtitle task completed.",
    });
    const wrapper = mount(App, {
      props: {
        createJob: vi.fn().mockResolvedValue(createdJob),
        getJob: vi.fn().mockResolvedValue(doneJob),
        getSubtitles: vi.fn().mockResolvedValue(timelineSubtitles),
        createJobEventSource: vi.fn().mockReturnValue(new FakeEventSource()),
        pollIntervalMs: 10,
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await vi.runOnlyPendingTimersAsync();
    await wrapper.vm.$nextTick();

    const topbar = wrapper.get('[data-testid="app-topbar"]').text();
    expect(topbar).toContain("已完成");
    expect(topbar).toContain("100%");
    expect(topbar).toContain("2 条字幕");
  });

  it("creates a job and polls until it is finished", async () => {
    vi.useFakeTimers();
    const createdJob = buildJob();
    const doneJob = buildJob({
      status: "done",
      progress: 100,
      message: "Subtitle task completed.",
    });
    const createJob = vi.fn().mockResolvedValue(createdJob);
    const getJob = vi.fn().mockResolvedValue(doneJob);
    const getSubtitles = vi.fn().mockResolvedValue(subtitles);
    const createJobEventSource = vi.fn().mockReturnValue(new FakeEventSource());
    const wrapper = mount(App, {
      props: {
        createJob,
        getJob,
        getSubtitles,
        createJobEventSource,
        pollIntervalMs: 10,
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await vi.runOnlyPendingTimersAsync();
    await wrapper.vm.$nextTick();

    expect(createJob).toHaveBeenCalledOnce();
    expect(getJob).toHaveBeenCalledWith("job_test");
    expect(getSubtitles).toHaveBeenCalledWith("job_test");
    expect(wrapper.text()).toContain("已完成");
    expect(wrapper.text()).toContain("Subtitle task completed.");
    expect(wrapper.get('[data-testid="live-subtitle"]').text()).toContain("Hello");
    expect(wrapper.get('[data-testid="live-subtitle"]').text()).toContain("你好");
    expect(wrapper.text()).toContain("Hello");
    expect(wrapper.text()).toContain("你好");
    expect(wrapper.get("video").attributes("src")).toBe("/api/jobs/job_test/video");
    expect(wrapper.get("a").attributes("href")).toBe("/api/jobs/job_test/srt");
  });

  it("appends subtitles from SSE events and closes the stream", async () => {
    const createdJob = buildJob();
    const createJob = vi.fn().mockResolvedValue(createdJob);
    const getJob = vi.fn();
    const getSubtitles = vi.fn();
    const eventSource = new FakeEventSource();
    const createJobEventSource = vi.fn().mockReturnValue(eventSource);
    const wrapper = mount(App, {
      props: {
        createJob,
        getJob,
        getSubtitles,
        createJobEventSource,
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("正在实时接收字幕");

    eventSource.emit({
      type: "subtitle_partial",
      job_id: "job_test",
      data: { cue: subtitles[0] },
    });
    eventSource.emit({
      type: "job_done",
      job_id: "job_test",
      data: {},
    });
    eventSource.emit({
      type: "job_closed",
      job_id: "job_test",
      data: {},
    });
    await wrapper.vm.$nextTick();

    expect(createJobEventSource).toHaveBeenCalledWith("job_test");
    expect(wrapper.get('[data-testid="live-subtitle"]').text()).toContain("Hello");
    expect(wrapper.get('[data-testid="live-subtitle"]').text()).toContain("你好");
    expect(wrapper.text()).toContain("Hello");
    expect(wrapper.text()).toContain("你好");
    expect(wrapper.text()).toContain("实时连接已关闭");
    expect(eventSource.closed).toBe(true);
    expect(getSubtitles).not.toHaveBeenCalled();
    expect(getJob).not.toHaveBeenCalled();
  });

  it("shows only target text in the live subtitle for target subtitle mode", async () => {
    const createdJob = buildJob({ subtitle_mode: "target" });
    const eventSource = new FakeEventSource();
    const wrapper = mount(App, {
      props: {
        createJob: vi.fn().mockResolvedValue(createdJob),
        getJob: vi.fn(),
        getSubtitles: vi.fn(),
        createJobEventSource: vi.fn().mockReturnValue(eventSource),
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await wrapper.vm.$nextTick();

    eventSource.emit({
      type: "subtitle_partial",
      job_id: "job_test",
      data: { cue: subtitles[0] },
    });
    await wrapper.vm.$nextTick();

    const liveSubtitleText = wrapper.get('[data-testid="live-subtitle"]').text();
    expect(liveSubtitleText).toContain("你好");
    expect(liveSubtitleText).not.toContain("Hello");
  });

  it("shows a translation pending state when target text is not ready", async () => {
    const createdJob = buildJob({ subtitle_mode: "target" });
    const eventSource = new FakeEventSource();
    const wrapper = mount(App, {
      props: {
        createJob: vi.fn().mockResolvedValue(createdJob),
        getJob: vi.fn(),
        getSubtitles: vi.fn(),
        createJobEventSource: vi.fn().mockReturnValue(eventSource),
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await wrapper.vm.$nextTick();

    eventSource.emit({
      type: "subtitle_partial",
      job_id: "job_test",
      data: {
        cue: {
          ...subtitles[0],
          target_text: "Hello",
          display_text: "Hello",
        },
      },
    });
    await wrapper.vm.$nextTick();

    const liveSubtitleText = wrapper.get('[data-testid="live-subtitle"]').text();
    expect(liveSubtitleText).toContain("正在翻译...");
    expect(liveSubtitleText).not.toContain("Hello");
  });

  it("loads subtitles when SSE completes without subtitle events", async () => {
    const createdJob = buildJob();
    const createJob = vi.fn().mockResolvedValue(createdJob);
    const getSubtitles = vi.fn().mockResolvedValue(subtitles);
    const eventSource = new FakeEventSource();
    const wrapper = mount(App, {
      props: {
        createJob,
        getJob: vi.fn(),
        getSubtitles,
        createJobEventSource: vi.fn().mockReturnValue(eventSource),
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await wrapper.vm.$nextTick();

    eventSource.emit({
      type: "job_done",
      job_id: "job_test",
      data: {},
    });
    eventSource.emit({
      type: "job_closed",
      job_id: "job_test",
      data: {},
    });
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(getSubtitles).toHaveBeenCalledWith("job_test");
    expect(wrapper.get('[data-testid="live-subtitle"]').text()).toContain("Hello");
    expect(wrapper.get('[data-testid="live-subtitle"]').text()).toContain("你好");
  });

  it("marks the current job failed when a failed SSE event arrives", async () => {
    const createdJob = buildJob({
      status: "transcribing",
      progress: 50,
      message: "Transcribing speech.",
    });
    const eventSource = new FakeEventSource();
    const wrapper = mount(App, {
      props: {
        createJob: vi.fn().mockResolvedValue(createdJob),
        getJob: vi.fn(),
        getSubtitles: vi.fn(),
        createJobEventSource: vi.fn().mockReturnValue(eventSource),
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await wrapper.vm.$nextTick();

    eventSource.emit({
      type: "job_failed",
      job_id: "job_test",
      data: { error: "ASR request failed." },
    });
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="app-topbar"]').text()).toContain("失败");
    expect(wrapper.get(".job-status-panel").text()).toContain("失败");
    expect(wrapper.text()).toContain("ASR request failed.");
  });

  it("links subtitle selection with the video timeline", async () => {
    vi.useFakeTimers();
    const createdJob = buildJob();
    const doneJob = buildJob({
      status: "done",
      progress: 100,
      message: "Subtitle task completed.",
    });
    const wrapper = mount(App, {
      props: {
        createJob: vi.fn().mockResolvedValue(createdJob),
        getJob: vi.fn().mockResolvedValue(doneJob),
        getSubtitles: vi.fn().mockResolvedValue(timelineSubtitles),
        createJobEventSource: vi.fn().mockReturnValue(new FakeEventSource()),
        pollIntervalMs: 10,
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await vi.runOnlyPendingTimersAsync();
    await wrapper.vm.$nextTick();

    const video = wrapper.get<HTMLVideoElement>("video");
    Object.defineProperty(video.element, "currentTime", {
      value: 15,
      writable: true,
      configurable: true,
    });
    await video.trigger("timeupdate");
    await wrapper.vm.$nextTick();

    const items = wrapper.findAll(".subtitle-item");
    expect(items[1].attributes("data-active")).toBe("true");

    await items[0].trigger("click");

    expect(video.element.currentTime).toBe(0.55);
  });

  it("highlights generated glossary terms in the subtitle list", async () => {
    vi.useFakeTimers();
    const createdJob = buildJob();
    const doneJob = buildJob({
      status: "done",
      progress: 100,
      message: "Subtitle task completed.",
    });
    const wrapper = mount(App, {
      props: {
        createJob: vi.fn().mockResolvedValue(createdJob),
        getJob: vi.fn().mockResolvedValue(doneJob),
        getSubtitles: vi.fn().mockResolvedValue([
          {
            ...subtitles[0],
            source_text: "Heat stress",
            target_text: "热应激",
          },
        ]),
        generateInsight: vi.fn().mockResolvedValue(insightWithTerm),
        createJobEventSource: vi.fn().mockReturnValue(new FakeEventSource()),
        pollIntervalMs: 10,
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await vi.runOnlyPendingTimersAsync();
    await wrapper.vm.$nextTick();
    await wrapper.get('[data-testid="result-tab-insight"]').trigger("click");
    await wrapper.vm.$nextTick();
    await wrapper.get('[data-testid="generate-insight"]').trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="video-glossary"]').text()).toContain("热应激");
    expect(wrapper.get('[data-testid="video-glossary"]').text()).toContain("heat stress");
    await wrapper.get('[data-testid="result-tab-subtitles"]').trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.get('[data-testid="term-highlight-Heat stress"]').text()).toBe("Heat stress");
    expect(wrapper.get('[data-testid="term-highlight-热应激"]').text()).toBe("热应激");
  });

  it("links video playback time with active insight items", async () => {
    vi.useFakeTimers();
    const createdJob = buildJob();
    const doneJob = buildJob({
      status: "done",
      progress: 100,
      message: "Subtitle task completed.",
    });
    const wrapper = mount(App, {
      props: {
        createJob: vi.fn().mockResolvedValue(createdJob),
        getJob: vi.fn().mockResolvedValue(doneJob),
        getSubtitles: vi.fn().mockResolvedValue(timelineSubtitles),
        generateInsight: vi.fn().mockResolvedValue(insightWithTerm),
        createJobEventSource: vi.fn().mockReturnValue(new FakeEventSource()),
        pollIntervalMs: 10,
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await vi.runOnlyPendingTimersAsync();
    await wrapper.vm.$nextTick();
    await wrapper.get('[data-testid="result-tab-insight"]').trigger("click");
    await wrapper.vm.$nextTick();
    await wrapper.get('[data-testid="generate-insight"]').trigger("click");
    await wrapper.vm.$nextTick();

    const video = wrapper.get<HTMLVideoElement>("video");
    Object.defineProperty(video.element, "currentTime", {
      value: 1,
      writable: true,
      configurable: true,
    });
    await video.trigger("timeupdate");
    await wrapper.vm.$nextTick();

    expect(wrapper.get('[data-testid="insight-item-key_point_1"]').attributes("data-active")).toBe(
      "true",
    );
  });

  it("shows an error when job creation fails", async () => {
    const createJob = vi.fn().mockRejectedValue(new Error("Upload failed."));
    const wrapper = mount(App, {
      props: {
        createJob,
      },
    });
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get("form").trigger("submit");
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Upload failed.");
    expect(wrapper.get('[role="alert"]').text()).toContain("Upload failed.");
  });
});
