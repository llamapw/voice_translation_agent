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
];

describe("SubtitleList", () => {
  it("shows an empty state when no cues exist", () => {
    const wrapper = mount(SubtitleList, {
      props: {
        cues: [],
      },
    });

    expect(wrapper.text()).toContain("暂无字幕");
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
});
