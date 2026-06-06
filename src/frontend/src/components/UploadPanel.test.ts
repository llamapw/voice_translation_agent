import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import UploadPanel from "./UploadPanel.vue";

describe("UploadPanel", () => {
  it("disables submit until a file is selected", () => {
    const wrapper = mount(UploadPanel);

    expect(wrapper.get('[data-testid="submit-upload"]').attributes("disabled")).toBeDefined();
  });

  it("emits submit payload with selected options", async () => {
    const wrapper = mount(UploadPanel);
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");
    await wrapper.get('[data-testid="source-language"]').setValue("en");
    await wrapper.get('[data-testid="target-language"]').setValue("zh");
    await wrapper.get('[data-testid="subtitle-mode"]').setValue("target");
    await wrapper.get('[data-testid="correct-text"]').setValue(false);
    await wrapper.get("form").trigger("submit");

    expect(wrapper.emitted("submit")?.[0]).toEqual([
      {
        file,
        source_language: "en",
        target_language: "zh",
        correct: false,
        asr_model: "paraformer-v2",
        llm_model: "default",
        subtitle_mode: "target",
      },
    ]);
  });

  it("shows a summary for the selected file", async () => {
    const wrapper = mount(UploadPanel);
    const file = new File(["demo"], "demo.mp4", { type: "video/mp4" });
    const fileInput = wrapper.get<HTMLInputElement>('[data-testid="video-file"]');

    Object.defineProperty(fileInput.element, "files", {
      value: [file],
      configurable: true,
    });

    await fileInput.trigger("change");

    const summary = wrapper.get('[data-testid="selected-file-summary"]').text();
    expect(summary).toContain("demo.mp4");
    expect(summary).toContain("video/mp4");
    expect(summary).toContain("4 B");
  });

  it("shows busy state while uploading", () => {
    const wrapper = mount(UploadPanel, {
      props: {
        isSubmitting: true,
      },
    });

    expect(wrapper.get('[data-testid="submit-upload"]').text()).toContain("上传中");
  });
});
