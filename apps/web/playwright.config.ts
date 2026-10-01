import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: process.env.CI ? 2 : 4,
  retries: 0,
  timeout: 45_000,
  projects: ["chromium", "firefox", "webkit"].map((browserName) => ({
    name: browserName,
    use: { browserName: browserName as "chromium" | "firefox" | "webkit" },
  })),
  use: {
    baseURL: process.env.PREVIEW_URL ?? "http://127.0.0.1:4173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: process.env.PREVIEW_URL
    ? undefined
    : {
        command: "node scripts/serve.mjs",
        url: "http://127.0.0.1:4173",
        reuseExistingServer: !process.env.CI,
      },
  reporter: [["list"], ["html", { open: "never" }]],
});
