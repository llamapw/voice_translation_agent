export type JobStatus =
  | "pending"
  | "extracting_audio"
  | "transcribing"
  | "correcting"
  | "translating"
  | "generating_subtitle"
  | "done"
  | "failed";

export type SubtitleMode = "source" | "target" | "bilingual";

export interface JobCreateOptions {
  source_language: string;
  target_language: string;
  correct: boolean;
  asr_model: string;
  llm_model: string;
  subtitle_mode: SubtitleMode;
}

export interface JobRead extends JobCreateOptions {
  id: string;
  status: JobStatus;
  progress: number;
  message: string;
  original_filename: string | null;
  input_extension: string;
  video_url: string | null;
  subtitle_url: string | null;
  srt_download_url: string | null;
  error: string | null;
}

export const statusLabel: Record<JobStatus, string> = {
  pending: "等待开始",
  extracting_audio: "提取音频中",
  transcribing: "语音识别中",
  correcting: "文本修正中",
  translating: "字幕翻译中",
  generating_subtitle: "生成字幕中",
  done: "已完成",
  failed: "失败",
};

export function isFinishedJob(job: JobRead): boolean {
  return job.status === "done" || job.status === "failed";
}

export function isRunningJob(job: JobRead): boolean {
  return !isFinishedJob(job) && job.status !== "pending";
}
