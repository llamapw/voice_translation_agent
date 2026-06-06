import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

import { resolveApiProxyTarget } from "./src/config/proxy";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/api": {
        target: resolveApiProxyTarget(process.env),
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
  },
});
