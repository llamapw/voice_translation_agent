import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SubtitlePanel from "./SubtitlePanel.vue";
import type { SubtitleCue } from "../types/subtitle";

const cues: SubtitleCue[] = [
  {
    index: 1,
    start: 0.55,
    end: 13.51,
    source_text: "Hello",
    target_text: "你好",
    display_text: "Hello\n你好",
  },
];

const timelineCues: SubtitleCue[] = [
  cues[0],
  {
    index: 2,
    start: 14,
    end: 18.5,
    source_text: "Next line",
    target_text: "下一句",
    display_text: "Next line\n下一句",
  },
];

describe("SubtitlePanel", () => {
  it("renders subtitle count and download link", () => {
    const wrapper = mount(SubtitlePanel, {
      props: {
        cues,
        srtUrl: "/api/jobs/job_test/srt",
      },
    });

    expect(wrapper.text()).toContain("1 条字幕");
    expect(wrapper.get("a").attributes("href")).toBe("/api/jobs/job_test/srt");
    expect(wrapper.get("a").attributes("download")).toBe("output.srt");
  });

  it("disables download copy when srt url is missing", () => {
    const wrapper = mount(SubtitlePanel, {
      props: {
        cues: [],
        srtUrl: null,
      },
    });

    expect(wrapper.text()).toContain("SRT 尚未生成");
  });

  it("renders timeline summary and active cue hint", () => {
    const wrapper = mount(SubtitlePanel, {
      props: {
        cues: timelineCues,
        srtUrl: null,
        activeCueIndex: 2,
      },
    });

    const summary = wrapper.get('[data-testid="subtitle-timeline-summary"]').text();

    expect(summary).toContain("2 条字幕");
    expect(summary).toContain("00:18.500");
    expect(summary).toContain("当前 #2");
  });

  it("passes active cue state and selected cues through", async () => {
    const wrapper = mount(SubtitlePanel, {
      props: {
        cues,
        srtUrl: null,
        activeCueIndex: 1,
      },
    });

    expect(wrapper.get(".subtitle-item").attributes("data-active")).toBe("true");

    await wrapper.get(".subtitle-item").trigger("click");

    expect(wrapper.emitted("select")?.[0]).toEqual([cues[0]]);
  });
});
