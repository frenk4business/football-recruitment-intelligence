import { chromium } from "playwright";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../../../", import.meta.url));
const phase = process.argv[2] ?? "after";
const dir = root + "artifacts/local-qa/player-images/";
mkdirSync(dir, { recursive: true });
const manifest = JSON.parse(
  readFileSync(root + "artifacts/player-images/manifest.json"),
);
const profiles = ["statsbomb:47521", "statsbomb:18999", "statsbomb:4642"].map(
  (id) => manifest.identities[id]?.profiles[0],
);
const browser = await chromium.launch();
const report = [];
for (const locale of ["en", "nl"])
  for (const width of [1440, 375]) {
    for (const view of ["players", "profile", "comparison", "recruitment"]) {
      const page = await browser.newPage({ viewport: { width, height: 960 } });
      const requests = [];
      page.on("request", (r) => requests.push(r.url()));
      await page.addInitScript(() => {
        window.imageCLS = 0;
        window.imageLCP = 0;
        new PerformanceObserver((l) => {
          for (const e of l.getEntries())
            if (!e.hadRecentInput) window.imageCLS += e.value;
        }).observe({ type: "layout-shift", buffered: true });
        new PerformanceObserver((l) => {
          for (const e of l.getEntries()) window.imageLCP = e.startTime;
        }).observe({ type: "largest-contentful-paint", buffered: true });
      });
      const path = view === "recruitment" ? "recruitment/" : "players/";
      const query =
        view === "profile"
          ? "?q=Alessia+Russo"
          : view === "comparison"
            ? `?profile=${profiles[0]}&compare=${profiles[1]}&compare2=${profiles[2]}`
            : "";
      const imageIndexReady =
        phase === "before"
          ? Promise.resolve()
          : page
              .waitForResponse((r) =>
                /\/players\/images\/index-[a-f0-9]+\.json$/.test(r.url()),
              )
              .then(async (response) => {
                if (!response.ok())
                  throw new Error("Image index unavailable during audit");
                await response.finished();
              });
      const started = performance.now();
      await page.goto(
        `${process.env.PREVIEW_URL ?? "http://127.0.0.1:4173"}/${locale === "nl" ? "nl/" : ""}${path}${query}`,
      );
      if (view === "recruitment")
        await page
          .locator('[data-feature="progressive_passes_per90"] select')
          .first()
          .selectOption("minimum");
      let profileOpen;
      if (view === "profile") {
        const result = page.locator(".profile-name").first();
        await result.waitFor();
        const clicked = performance.now();
        await result.click();
        await page.locator(".profile-metrics").first().waitFor();
        profileOpen = performance.now() - clicked;
      }
      await page
        .locator(
          view === "players"
            ? ".profile-name"
            : view === "recruitment"
              ? ".recruitment-table tbody tr"
              : ".profile-metrics",
        )
        .first()
        .waitFor();
      const ready = performance.now() - started;
      if (view === "recruitment")
        await page.locator(".recruitment-table").scrollIntoViewIfNeeded();
      if (view === "comparison")
        await page.locator(".profile-metrics").first().scrollIntoViewIfNeeded();
      await imageIndexReady;
      // Readiness was recorded above; now include all settled visible-view traffic.
      await page.waitForLoadState("networkidle");
      await page.screenshot({
        path: `${dir}${phase}-${locale}-${width}-${view}.png`,
      });
      const metrics = await page.evaluate(() => ({
        cls: window.imageCLS,
        lcp_ms: window.imageLCP,
        overflow: document.documentElement.scrollWidth > innerWidth,
        imageIndexRequests: performance
          .getEntriesByType("resource")
          .filter((r) =>
            /\/players\/images\/index-[a-f0-9]+\.json$/.test(r.name),
          ).length,
        imageIndexDecodedBytes: performance
          .getEntriesByType("resource")
          .filter((r) =>
            /\/players\/images\/index-[a-f0-9]+\.json$/.test(r.name),
          )
          .reduce((n, r) => n + r.decodedBodySize, 0),
        transfer: [
          ...performance.getEntriesByType("navigation"),
          ...performance.getEntriesByType("resource"),
        ].reduce((a, r) => a + r.transferSize, 0),
        images: performance
          .getEntriesByType("resource")
          .filter(
            (r) =>
              r.name.endsWith(".webp") && r.name.includes("/players/images/"),
          ).length,
        imagesBytes: performance
          .getEntriesByType("resource")
          .filter(
            (r) =>
              r.name.endsWith(".webp") && r.name.includes("/players/images/"),
          )
          .reduce((a, r) => a + r.transferSize, 0),
      }));
      if (phase !== "before" && metrics.imageIndexRequests !== 1)
        throw new Error(
          "Image index missing or duplicated in view traffic audit",
        );
      report.push({
        locale,
        width,
        view,
        ready_ms: ready,
        profile_open_ms: profileOpen,
        ...metrics,
        external: requests.filter((u) => /wikidata.org|wikimedia.org/.test(u)),
      });
      await page.close();
    }
  }
await browser.close();
writeFileSync(`${dir}${phase}.json`, JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report, null, 2));
