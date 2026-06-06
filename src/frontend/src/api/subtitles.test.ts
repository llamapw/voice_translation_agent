import { afterEach, describe, expect, it, vi } from "vitest";

import { getSubtitles } from "./subtitles";
import type { SubtitleCue } from "../types/subtitle";

const subtitles: SubtitleCue[] = [
  {
    index: 1,
    start: 0.55,
    end: 13.51,
    source_text: "Hello",
    target_text: "你好",
    display_text: "Hello\n你好",
  },
];

function mockResponse(payload: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

describe("subtitles api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("reads subtitles by job id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockResponse(subtitles));

    await expect(getSubtitles("job_test", fetchMock)).resolves.toEqual(subtitles);
    expect(fetchMock).toHaveBeenCalledWith("/api/jobs/job_test/subtitles");
  });

  it("throws a readable error when subtitles are unavailable", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockResponse({ detail: "Subtitles not found." }, false, 404),
    );

    await expect(getSubtitles("job_test", fetchMock)).rejects.toThrow("Subtitles not found.");
  });
});
