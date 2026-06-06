import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App.vue";
import type { JobEvent } from "./api/jobEvents";
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
    expect(wrapper.text()).toContain("Hello");
    expect(wrapper.text()).toContain("你好");
    expect(eventSource.closed).toBe(true);
    expect(getSubtitles).not.toHaveBeenCalled();
    expect(getJob).not.toHaveBeenCalled();
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
  });
});
