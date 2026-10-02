import { chromium } from "playwright";
import { writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { git } from "./release-common.mjs";
const base = process.env.PREVIEW_URL ?? "http://127.0.0.1:4173";
const browser = await chromium.launch();
const rows = [];
try {
  for (const path of [
    "/",
    "/players/",
    "/player-dna/",
    "/translation/",
    "/recruitment/",
    "/methodology/",
  ])
    for (let run = 1; run <= 3; run++) {
      const context = await browser.newContext({
        viewport: { width: 375, height: 812 },
        deviceScaleFactor: 1,
        isMobile: true,
      });
      const page = await context.newPage();
      const cdp = await context.newCDPSession(page);
      await cdp.send("Network.enable");
      await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
      await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
      await cdp.send("Network.emulateNetworkConditions", {
        offline: false,
        latency: 150,
        downloadThroughput: 200000,
        uploadThroughput: 93750,
      });
      await page.addInitScript(() => {
        globalThis.__friPerformance = { lcp: 0, cls: 0, blocking: 0 };
        new PerformanceObserver((list) => {
          for (const e of list.getEntries())
            globalThis.__friPerformance.lcp = e.startTime;
        }).observe({ type: "largest-contentful-paint", buffered: true });
        new PerformanceObserver((list) => {
          for (const e of list.getEntries())
            if (!e.hadRecentInput) globalThis.__friPerformance.cls += e.value;
        }).observe({ type: "layout-shift", buffered: true });
        new PerformanceObserver((list) => {
          for (const e of list.getEntries())
            globalThis.__friPerformance.blocking += Math.max(
              0,
              e.duration - 50,
            );
        }).observe({ type: "longtask", buffered: true });
      });
      let transfer = 0;
      const responses = [];
      const bodies = [];
      cdp.on("Network.loadingFinished", (e) => {
        transfer += e.encodedDataLength;
      });
      page.on("response", (r) => {
        if (/\.(js|json)(\?|$)/.test(r.url()))
          bodies.push(
            r
              .body()
              .then((b) =>
                responses.push({
                  path: new URL(r.url()).pathname,
                  decoded: b.length,
                  gzip: gzipSync(b).length,
                }),
              )
              .catch(() => {}),
          );
      });
      await page.goto(base + path);
      await page.waitForTimeout(5000);
      await Promise.all(bodies);
      const row = await page.evaluate(() => ({
        ...globalThis.__friPerformance,
        overflow: document.documentElement.scrollWidth > innerWidth,
        requests: performance.getEntriesByType("resource").length,
      }));
      Object.assign(row, {
        path,
        run,
        transfer_bytes: transfer,
        js_gzip_bytes: responses
          .filter((r) => r.path.endsWith(".js"))
          .reduce((s, r) => s + r.gzip, 0),
        json_decoded_bytes: responses
          .filter((r) => r.path.endsWith(".json"))
          .reduce((s, r) => s + r.decoded, 0),
        responses,
      });
      if (path === "/recruitment/") {
        const selector = page.getByRole("combobox", {
          name: "Role",
          exact: true,
        });
        await selector.evaluate((e) => {
          globalThis.__friInteractionStart = performance.now();
          e.value = "MID";
          e.dispatchEvent(new Event("change", { bubbles: true }));
        });
        await page.locator(".native-results > li").first().waitFor();
        row.interaction_ms = await page.evaluate(
          () => performance.now() - globalThis.__friInteractionStart,
        );
      }
      rows.push(row);
      console.log(
        path,
        run,
        JSON.stringify({
          lcp: row.lcp,
          cls: row.cls,
          blocking: row.blocking,
          bytes: row.transfer_bytes,
          interaction: row.interaction_ms,
        }),
      );
      await context.close();
    }
} finally {
  await browser.close();
}
const median = (xs) => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)];
const summary = [...new Set(rows.map((r) => r.path))].map((path) => {
  const sample = rows.filter((r) => r.path === path);
  return {
    path,
    lcp_median_ms: median(sample.map((r) => r.lcp)),
    cls_max: Math.max(...sample.map((r) => r.cls)),
    blocking_median_ms: median(sample.map((r) => r.blocking)),
    js_gzip_max: Math.max(...sample.map((r) => r.js_gzip_bytes)),
    json_decoded_max: Math.max(...sample.map((r) => r.json_decoded_bytes)),
    transfer_max: Math.max(...sample.map((r) => r.transfer_bytes)),
    interaction_median_ms:
      path === "/recruitment/"
        ? median(sample.map((r) => r.interaction_ms))
        : null,
    overflow: sample.some((r) => r.overflow),
  };
});
const failures = summary.filter(
  (r) =>
    r.lcp_median_ms >= 2500 ||
    r.cls_max >= 0.1 ||
    r.blocking_median_ms >= 300 ||
    r.js_gzip_max > 250000 ||
    r.json_decoded_max >
      (r.path === "/players/"
        ? 3_000_000
        : r.path === "/recruitment/"
          ? 1_500_000
          : 350000) ||
    r.transfer_max > 750000 ||
    (r.interaction_median_ms ?? 0) >= 200 ||
    r.overflow,
);
const report = {
  commit: git("rev-parse", "HEAD"),
  base,
  timestamp: new Date().toISOString(),
  profile:
    "Chromium, 375x812, cold cache, 4x CPU, 1.6Mbps down/750Kbps up,150ms latency; 5 seconds after load; 3 runs; gzip bytes recomputed at default level",
  summary,
  rows,
  passed: failures.length === 0,
};
writeFileSync(
  process.env.PERFORMANCE_REPORT ?? "/tmp/fri-v12-performance.json",
  JSON.stringify(report, null, 2) + "\n",
);
console.log(JSON.stringify(summary, null, 2));
if (failures.length)
  throw new Error(
    `Performance gate failed: ${failures.map((r) => r.path).join(", ")}`,
  );
