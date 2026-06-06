import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import JobStatus from "./JobStatus.vue";
import type { JobRead } from "../types/job";

function buildJob(overrides: Partial<JobRead> = {}): JobRead {
  return {
    id: "job_test",
    status: "transcribing",
    progress: 50,
    message: "Transcribing speech.",
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

describe("JobStatus", () => {
  it("shows an empty state before a job exists", () => {
    const wrapper = mount(JobStatus, {
      props: {
        job: null,
      },
    });

    expect(wrapper.text()).toContain("等待上传任务");
  });

  it("renders status label, progress, message, and job id", () => {
    const wrapper = mount(JobStatus, {
      props: {
        job: buildJob(),
      },
    });

    expect(wrapper.text()).toContain("语音识别中");
    expect(wrapper.text()).toContain("50%");
    expect(wrapper.text()).toContain("Transcribing speech.");
    expect(wrapper.text()).toContain("job_test");
    expect(wrapper.get('[data-testid="job-progress"]').attributes("style")).toContain("width: 50%");
  });

  it("renders task configuration details", () => {
    const wrapper = mount(JobStatus, {
      props: {
        job: buildJob({
          source_language: "en",
          target_language: "zh",
          subtitle_mode: "bilingual",
          asr_model: "paraformer-v2",
        }),
      },
    });

    expect(wrapper.get('[data-testid="job-config-summary"]').text()).toContain("en → zh");
    expect(wrapper.get('[data-testid="job-config-summary"]').text()).toContain("bilingual");
    expect(wrapper.get('[data-testid="job-config-summary"]').text()).toContain("paraformer-v2");
  });

  it("shows backend error when job failed", () => {
    const wrapper = mount(JobStatus, {
      props: {
        job: buildJob({
          status: "failed",
          progress: 100,
          message: "Task failed.",
          error: "ASR request failed.",
        }),
      },
    });

    expect(wrapper.text()).toContain("失败");
    expect(wrapper.text()).toContain("ASR request failed.");
  });
});
