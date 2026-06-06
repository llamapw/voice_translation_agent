import { readJsonResponse, type Fetcher } from "./jobs";
import type { SubtitleCue } from "../types/subtitle";

export async function getSubtitles(
  jobId: string,
  fetcher: Fetcher = fetch,
): Promise<SubtitleCue[]> {
  const response = await fetcher(
    "/api/jobs/{0}/subtitles".replace("{0}", encodeURIComponent(jobId)),
  );

  return readJsonResponse<SubtitleCue[]>(response);
}
