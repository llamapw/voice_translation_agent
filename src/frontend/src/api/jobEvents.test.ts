import { describe, expect, it, vi } from "vitest";

import { createJobEventSource, parseJobEvent, type JobEvent } from "./jobEvents";

describe("jobEvents api", () => {
  it("creates EventSource for job events endpoint", () => {
    const eventSourceFactory = vi.fn();

    createJobEventSource("job_test", eventSourceFactory);

    expect(eventSourceFactory).toHaveBeenCalledWith("/api/jobs/job_test/events");
  });

  it("parses job event payload", () => {
    const event: JobEvent = parseJobEvent(
      JSON.stringify({
        type: "subtitle_partial",
        job_id: "job_test",
        data: {
          cue: {
            index: 1,
            start: 0,
            end: 1,
            source_text: "Hello",
            target_text: "你好",
            display_text: "Hello\n你好",
          },
        },
      }),
    );

    expect(event.type).toBe("subtitle_partial");
    expect(event.data.cue?.target_text).toBe("你好");
  });

  it("parses subtitle translation delta payload", () => {
    const event: JobEvent = parseJobEvent(
      JSON.stringify({
        type: "subtitle_translation_delta",
        job_id: "job_test",
        data: {
          cue_index: 1,
          delta: "你",
          text: "你",
        },
      }),
    );

    expect(event.type).toBe("subtitle_translation_delta");
    expect(event.data.cue_index).toBe(1);
    expect(event.data.delta).toBe("你");
    expect(event.data.text).toBe("你");
  });
});
