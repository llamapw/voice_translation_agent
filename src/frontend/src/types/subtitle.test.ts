import { describe, expect, it } from "vitest";

import { formatCueTime, type SubtitleCue } from "./subtitle";

describe("subtitle types helpers", () => {
  it("formats cue timestamps for display", () => {
    expect(formatCueTime(65.432)).toBe("01:05.432");
  });

  it("allows display_text to be absent because backend can derive it", () => {
    const cue: SubtitleCue = {
      index: 1,
      start: 0.55,
      end: 13.51,
      source_text: "Hello",
      target_text: "你好",
      display_text: null,
    };

    expect(cue.display_text).toBeNull();
  });
});
