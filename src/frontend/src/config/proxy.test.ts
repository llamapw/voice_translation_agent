import { describe, expect, it } from "vitest";

import { resolveApiProxyTarget } from "./proxy";

describe("resolveApiProxyTarget", () => {
  it("uses the default backend proxy target", () => {
    expect(resolveApiProxyTarget({})).toBe("http://127.0.0.1:8010");
  });

  it("allows the backend proxy target to be configured", () => {
    expect(
      resolveApiProxyTarget({
        VITE_API_PROXY_TARGET: "http://127.0.0.1:8011",
      }),
    ).toBe("http://127.0.0.1:8011");
  });
});
