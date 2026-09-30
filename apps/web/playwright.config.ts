import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: process.env.PREVIEW_URL ?? "http://127.0.0.1:4173",
    browserName: "chromium",
  },
  webServer: process.env.PREVIEW_URL
    ? undefined
    : {
        command: "python3 -m http.server 4173 --bind 127.0.0.1 --directory out",
        url: "http://127.0.0.1:4173",
        reuseExistingServer: true,
      },
  reporter: "list",
});
