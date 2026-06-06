import type { JobCreateOptions, JobRead } from "../types/job";

export type Fetcher = typeof fetch;

export interface CreateJobInput extends JobCreateOptions {
  file: File;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function readJsonResponse<T>(response: Response): Promise<T> {
  const payload = await response.json();

  if (!response.ok) {
    const message =
      typeof payload?.detail === "string"
        ? payload.detail
        : "Request failed with status {0}.".replace("{0}", String(response.status));
    throw new ApiError(message, response.status);
  }

  return payload as T;
}

export async function createJob(input: CreateJobInput, fetcher: Fetcher = fetch): Promise<JobRead> {
  const body = new FormData();
  body.append("file", input.file);
  body.append("source_language", input.source_language);
  body.append("target_language", input.target_language);
  body.append("correct", String(input.correct));
  body.append("asr_model", input.asr_model);
  body.append("llm_model", input.llm_model);
  body.append("subtitle_mode", input.subtitle_mode);

  const response = await fetcher("/api/jobs", {
    method: "POST",
    body,
  });

  return readJsonResponse<JobRead>(response);
}

export async function getJob(jobId: string, fetcher: Fetcher = fetch): Promise<JobRead> {
  const response = await fetcher("/api/jobs/{0}".replace("{0}", encodeURIComponent(jobId)));

  return readJsonResponse<JobRead>(response);
}

export function buildVideoUrl(job: JobRead): string | null {
  return job.video_url;
}

export function buildSrtDownloadUrl(job: JobRead): string | null {
  return job.srt_download_url;
}
