import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App.vue";
import type { JobRead } from "./types/job";

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
    const wrapper = mount(App, {
      props: {
        createJob,
        getJob,
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
    expect(wrapper.text()).toContain("已完成");
    expect(wrapper.text()).toContain("Subtitle task completed.");
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
