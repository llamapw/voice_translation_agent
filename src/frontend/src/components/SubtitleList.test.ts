import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SubtitleList from "./SubtitleList.vue";
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
  {
    index: 2,
    start: 14.0,
    end: 18.5,
    source_text: "Next line",
    target_text: "下一句",
    display_text: "Next line\n下一句",
  },
];

describe("SubtitleList", () => {
  it("shows an empty state when no cues exist", () => {
    const wrapper = mount(SubtitleList, {
      props: {
        cues: [],
      },
    });

    const guide = wrapper.get('[data-testid="subtitle-empty-guide"]');

    expect(guide.text()).toContain("上传视频");
    expect(guide.text()).toContain("实时生成字幕");
    expect(guide.text()).toContain("播放联动与导出");
  });

  it("renders cue index, time, and bilingual text", () => {
    const wrapper = mount(SubtitleList, {
      props: {
        cues,
      },
    });

    expect(wrapper.text()).toContain("#1");
    expect(wrapper.text()).toContain("00:00.550");
    expect(wrapper.text()).toContain("00:13.510");
    expect(wrapper.text()).toContain("Hello");
    expect(wrapper.text()).toContain("你好");
  });

  it("marks the active cue and emits selected cues", async () => {
    const wrapper = mount(SubtitleList, {
      props: {
        cues,
        activeCueIndex: 2,
      },
    });

    const items = wrapper.findAll(".subtitle-item");
    expect(items[1].attributes("data-active")).toBe("true");
    expect(items[1].attributes("aria-current")).toBe("true");

    await items[0].trigger("click");

    expect(wrapper.emitted("select")?.[0]).toEqual([cues[0]]);
  });

  it("shows the duration of each cue", () => {
    const wrapper = mount(SubtitleList, {
      props: {
        cues,
      },
    });

    expect(wrapper.get('[data-testid="cue-duration-1"]').text()).toContain("12.96s");
  });

  it("highlights glossary terms in subtitle text", () => {
    const wrapper = mount(SubtitleList, {
      props: {
        cues: [
          {
            ...cues[0],
            source_text: "Compensable heat stress",
            target_text: "可补偿热应激",
          },
        ],
        terms: ["heat stress", "可补偿热应激"],
      },
    });

    expect(wrapper.get('[data-testid="term-highlight-heat stress"]').text()).toBe(
      "heat stress",
    );
    expect(wrapper.get('[data-testid="term-highlight-可补偿热应激"]').text()).toBe(
      "可补偿热应激",
    );
  });
});
