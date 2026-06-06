import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import InsightPanel from "./InsightPanel.vue";
import type { InsightRead } from "../types/insight";

const insight: InsightRead = {
  job_id: "job_test",
  summary: "运动会产生热量。汗液帮助身体降温。",
  items: [
    {
      id: "key_point_1",
      type: "key_point",
      title: "运动产生热量",
      content: "运动时大部分能量会转化为热量。",
      start: 0.55,
      end: 13.51,
      source_cue_indexes: [1],
    },
    {
      id: "term_1",
      type: "term",
      title: "可补偿热应激",
      content: "身体可以及时散热的状态。",
      start: 4,
      end: 10,
      source_cue_indexes: [1],
    },
  ],
  markdown_url: "/api/jobs/job_test/insights/markdown",
};

describe("InsightPanel", () => {
  it("shows an empty state before insight is generated", () => {
    const wrapper = mount(InsightPanel, {
      props: {
        insight: null,
        isLoading: false,
      },
    });

    expect(wrapper.text()).toContain("暂无知识笔记");
  });

  it("shows loading state while insight is being generated", () => {
    const wrapper = mount(InsightPanel, {
      props: {
        insight: null,
        isLoading: true,
      },
    });

    expect(wrapper.text()).toContain("正在生成知识笔记");
  });

  it("renders summary, grouped items, timestamps, and markdown download", () => {
    const wrapper = mount(InsightPanel, {
      props: {
        insight,
        isLoading: false,
      },
    });

    expect(wrapper.text()).toContain("知识笔记");
    expect(wrapper.text()).toContain("运动会产生热量。汗液帮助身体降温。");
    expect(wrapper.text()).toContain("关键要点");
    expect(wrapper.text()).toContain("术语");
    expect(wrapper.text()).toContain("00:00.550");
    expect(wrapper.text()).toContain("运动产生热量");
    expect(wrapper.text()).toContain("来源字幕: 1");
    expect(wrapper.find("a").attributes("href")).toBe("/api/jobs/job_test/insights/markdown");
  });

  it("emits selected insight items", async () => {
    const wrapper = mount(InsightPanel, {
      props: {
        insight,
        isLoading: false,
      },
    });

    await wrapper.findAll(".insight-item")[0].trigger("click");

    expect(wrapper.emitted("select-item")?.[0]).toEqual([insight.items[0]]);
  });
});
