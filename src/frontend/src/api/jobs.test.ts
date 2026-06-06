import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  buildSrtDownloadUrl,
  buildVideoUrl,
  createJob,
  getJob,
  type CreateJobInput,
} from "./jobs";
import type { JobRead } from "../types/job";

const job: JobRead = {
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
};

function mockResponse(payload: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

describe("jobs api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("creates a job with multipart form data", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(job));
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const input: CreateJobInput = {
      file,
      source_language: "zh",
      target_language: "zh",
      correct: true,
      asr_model: "paraformer-v2",
      llm_model: "default",
      subtitle_mode: "bilingual",
    };

    const result = await createJob(input, fetchMock);

    expect(result).toEqual(job);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/jobs",
      expect.objectContaining({
        method: "POST",
        body: expect.any(FormData),
      }),
    );
    const body = fetchMock.mock.calls[0][1].body as FormData;
    expect(body.get("file")).toBe(file);
    expect(body.get("source_language")).toBe("zh");
    expect(body.get("correct")).toBe("true");
  });

  it("reads a job by id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(job));

    await expect(getJob("job_test", fetchMock)).resolves.toEqual(job);
    expect(fetchMock).toHaveBeenCalledWith("/api/jobs/job_test");
  });

  it("throws ApiError when backend returns an error response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockResponse({ detail: "Job not found." }, false, 404),
    );

    const request = getJob("missing", fetchMock);

    await expect(request).rejects.toBeInstanceOf(ApiError);
    await expect(request).rejects.toThrow("Job not found.");
  });

  it("builds media and download urls from job payload", () => {
    expect(buildVideoUrl(job)).toBe("/api/jobs/job_test/video");
    expect(buildSrtDownloadUrl(job)).toBe("/api/jobs/job_test/srt");
  });
});
