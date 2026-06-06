import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import VideoPlayer from "./VideoPlayer.vue";

describe("VideoPlayer", () => {
  it("shows an empty state without a video url", () => {
    const wrapper = mount(VideoPlayer, {
      props: {
        videoUrl: null,
        title: null,
      },
    });

    expect(wrapper.text()).toContain("等待视频生成");
  });

  it("renders a playable video when url exists", () => {
    const wrapper = mount(VideoPlayer, {
      props: {
        videoUrl: "/api/jobs/job_test/video",
        title: "demo.mp4",
      },
    });

    expect(wrapper.get("video").attributes("src")).toBe("/api/jobs/job_test/video");
    expect(wrapper.text()).toContain("demo.mp4");
  });
});
