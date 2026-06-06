import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import App from "./App.vue";

describe("App", () => {
  it("renders the frontend shell", () => {
    const wrapper = mount(App);

    expect(wrapper.text()).toContain("Voice Translation Agent");
  });
});
