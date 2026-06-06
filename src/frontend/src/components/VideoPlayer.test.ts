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

  it("shows playback time and duration after metadata loads", async () => {
    const wrapper = mount(VideoPlayer, {
      props: {
        videoUrl: "/api/jobs/job_test/video",
        title: "demo.mp4",
      },
    });
    const video = wrapper.get<HTMLVideoElement>("video");

    Object.defineProperty(video.element, "duration", {
      value: 65.25,
      configurable: true,
    });

    await video.trigger("loadedmetadata");

    expect(wrapper.get('[data-testid="video-time-display"]').text()).toContain(
      "00:00.000 / 01:05.250",
    );
  });

  it("emits current playback time when the video updates", async () => {
    const wrapper = mount(VideoPlayer, {
      props: {
        videoUrl: "/api/jobs/job_test/video",
        title: "demo.mp4",
      },
    });
    const video = wrapper.get<HTMLVideoElement>("video");

    Object.defineProperty(video.element, "currentTime", {
      value: 12.5,
      configurable: true,
    });

    await video.trigger("timeupdate");

    expect(wrapper.emitted("timeupdate")?.[0]).toEqual([12.5]);
    expect(wrapper.get('[data-testid="video-time-display"]').text()).toContain("00:12.500");
  });

  it("seeks the video to a requested time", async () => {
    const wrapper = mount(VideoPlayer, {
      props: {
        videoUrl: "/api/jobs/job_test/video",
        title: "demo.mp4",
      },
    });
    const video = wrapper.get<HTMLVideoElement>("video");

    await wrapper.vm.seekTo(12.5);

    expect(video.element.currentTime).toBe(12.5);
  });
});
