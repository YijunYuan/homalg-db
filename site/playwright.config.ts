import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: 0,
  workers: 2,
  reporter: "list",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 },
      },
    },
  ],
  webServer: [
    {
      command: "npm run preview -- --port 4173 --strictPort",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: !process.env.CI,
    },
    {
      command:
        "uv run --project ../tools --extra serve homalg build-db --data site/fixtures/data --out build/site-e2e.sqlite && uv run --project ../tools --extra serve homalg serve --static site/dist --db build/site-e2e.sqlite --port 8788",
      url: "http://127.0.0.1:8788/api/manifest",
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  ],
});
