import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildInsightMarkdownUrl,
  generateInsight,
  getInsight,
  getInsightMarkdown,
} from "./insights";
import type { InsightRead } from "../types/insight";

const insight: InsightRead = {
  job_id: "job_test",
  summary: "运动会产生热量。",
  items: [
    {
      id: "key_point_1",
      type: "key_point",
      title: "片段 1",
      content: "运动会产生热量。",
      start: 0.55,
      end: 13.51,
      source_cue_indexes: [1],
    },
  ],
  markdown_url: "/api/jobs/job_test/insights/markdown",
};

function mockJsonResponse(payload: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

function mockTextResponse(payload: string, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue({ detail: payload }),
    text: vi.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

describe("insights api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("generates insight for a job", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockJsonResponse(insight));

    await expect(generateInsight("job_test", fetchMock)).resolves.toEqual(insight);
    expect(fetchMock).toHaveBeenCalledWith("/api/jobs/job_test/insights", {
      method: "POST",
    });
  });

  it("reads generated insight by job id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockJsonResponse(insight));

    await expect(getInsight("job_test", fetchMock)).resolves.toEqual(insight);
    expect(fetchMock).toHaveBeenCalledWith("/api/jobs/job_test/insights");
  });

  it("downloads generated insight markdown text", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockTextResponse("# 视频知识笔记\n"));

    await expect(getInsightMarkdown("job_test", fetchMock)).resolves.toBe("# 视频知识笔记\n");
    expect(fetchMock).toHaveBeenCalledWith("/api/jobs/job_test/insights/markdown");
  });

  it("throws a readable error when insight is unavailable", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockJsonResponse({ detail: "Insight not found." }, false, 404),
    );

    await expect(getInsight("missing", fetchMock)).rejects.toThrow("Insight not found.");
  });

  it("builds markdown download url from insight payload or job id", () => {
    expect(buildInsightMarkdownUrl("job_test", insight)).toBe(
      "/api/jobs/job_test/insights/markdown",
    );
    expect(buildInsightMarkdownUrl("job_without_payload")).toBe(
      "/api/jobs/job_without_payload/insights/markdown",
    );
  });
});
