import type { JobStatus } from "../types/job";
import type { SubtitleCue } from "../types/subtitle";

export type JobEventType =
  | "job_status"
  | "subtitle_partial"
  | "job_done"
  | "job_failed"
  | "job_closed";

export interface JobEvent {
  type: JobEventType;
  job_id: string;
  data: {
    status?: JobStatus;
    progress?: number;
    message?: string;
    cue?: SubtitleCue;
    error?: string;
  };
}

export type EventSourceFactory = (url: string) => EventSource;

export function createJobEventSource(
  jobId: string,
  eventSourceFactory: EventSourceFactory = (url) => new EventSource(url),
): EventSource {
  return eventSourceFactory(
    "/api/jobs/{0}/events".replace("{0}", encodeURIComponent(jobId)),
  );
}

export function parseJobEvent(payload: string): JobEvent {
  return JSON.parse(payload) as JobEvent;
}
