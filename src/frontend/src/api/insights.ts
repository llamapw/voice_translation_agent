import { ApiError, readJsonResponse, type Fetcher } from "./jobs";
import type { InsightRead } from "../types/insight";


function buildInsightUrl(jobId: string): string {
  return "/api/jobs/{0}/insights".replace("{0}", encodeURIComponent(jobId));
}

export function buildInsightMarkdownUrl(jobId: string, insight?: InsightRead): string {
  return insight?.markdown_url ?? "{0}/markdown".replace("{0}", buildInsightUrl(jobId));
}

export async function generateInsight(
  jobId: string,
  fetcher: Fetcher = fetch,
): Promise<InsightRead> {
  const response = await fetcher(buildInsightUrl(jobId), {
    method: "POST",
  });

  return readJsonResponse<InsightRead>(response);
}

export async function getInsight(
  jobId: string,
  fetcher: Fetcher = fetch,
): Promise<InsightRead> {
  const response = await fetcher(buildInsightUrl(jobId));

  return readJsonResponse<InsightRead>(response);
}

export async function getInsightMarkdown(
  jobId: string,
  fetcher: Fetcher = fetch,
): Promise<string> {
  const response = await fetcher(buildInsightMarkdownUrl(jobId));

  if (!response.ok) {
    const payload = await response.json();
    const message =
      typeof payload?.detail === "string"
        ? payload.detail
        : "Request failed with status {0}.".replace("{0}", String(response.status));
    throw new ApiError(message, response.status);
  }

  return response.text();
}
