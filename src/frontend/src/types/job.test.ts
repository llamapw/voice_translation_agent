import { describe, expect, it } from "vitest";

import { isFinishedJob, isRunningJob, statusLabel, type JobRead } from "./job";

function buildJob(status: JobRead["status"]): JobRead {
  return {
    id: "job_test",
    status,
    progress: status === "done" ? 100 : 50,
    message: "Testing",
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
  };
}

describe("job types helpers", () => {
  it("treats done and failed jobs as finished", () => {
    expect(isFinishedJob(buildJob("done"))).toBe(true);
    expect(isFinishedJob(buildJob("failed"))).toBe(true);
    expect(isFinishedJob(buildJob("transcribing"))).toBe(false);
  });

  it("detects running jobs while backend processing is active", () => {
    expect(isRunningJob(buildJob("extracting_audio"))).toBe(true);
    expect(isRunningJob(buildJob("done"))).toBe(false);
  });

  it("maps backend status values to readable labels", () => {
    expect(statusLabel.done).toBe("已完成");
    expect(statusLabel.transcribing).toBe("语音识别中");
  });
});
