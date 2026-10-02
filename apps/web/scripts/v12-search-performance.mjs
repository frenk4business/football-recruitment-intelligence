import { chromium } from "playwright";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { cpus, platform, arch } from "node:os";
import { performance } from "node:perf_hooks";
import {
  filterProfiles,
  defaults,
  profileSearchText,
} from "../src/lib/player-search.ts";
const imageAudit = process.argv.includes("--images");
const root = new URL("../../../", import.meta.url);
if (imageAudit)
  mkdirSync(new URL("artifacts/local-qa/player-images/", root), {
    recursive: true,
  });
const index = JSON.parse(
  readFileSync(new URL("artifacts/v12/public/index.json", root)),
);
const names = new Map(
  index.profiles.map((p) => [p.id, profileSearchText(index, p)]),
);
const quantile = (rows, p) =>
  [...rows].sort((a, b) => a - b)[
    Math.min(rows.length - 1, Math.floor(rows.length * p))
  ];
const timings = [];
for (let i = 0; i < 250; i++) {
  const start = performance.now();
  filterProfiles(
    index,
    {
      ...defaults,
      q: i % 2 ? "a" : "e",
      provider: i % 3 ? "wyscout" : "",
      minutes: "900",
    },
    names,
  );
  timings.push(performance.now() - start);
}
const browser = await chromium.launch();
const rows = [];
try {
  for (const locale of ["en", "nl"])
    for (const width of [1440, 375]) {
      const context = await browser.newContext({
        viewport: { width, height: 900 },
      });
      const page = await context.newPage();
      const responses = [],
        bodies = [];
      page.on("response", (r) => {
        if (r.url().startsWith("http"))
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
      const url =
        (process.env.PREVIEW_URL ?? "http://127.0.0.1:4173") +
        (locale === "en" ? "/players/" : "/nl/players/");
      const imageIndexReady = imageAudit
        ? page
            .waitForResponse((r) =>
              /\/players\/images\/index-[a-f0-9]+\.json$/.test(r.url()),
            )
            .then(async (response) => {
              if (!response.ok())
                throw new Error("Image index unavailable during audit");
              await response.finished();
            })
        : Promise.resolve();
      await page.goto(url);
      await page.locator(".profile-list > li").nth(49).waitFor();
      if (imageAudit) {
        await imageIndexReady;
        // This measures complete initial traffic, not time-to-interactive.
        await page.waitForLoadState("networkidle");
      }
      await Promise.all(bodies);
      const initial = [...responses];
      if (
        imageAudit &&
        initial.filter((r) =>
          /\/players\/images\/index-[a-f0-9]+\.json$/.test(r.path),
        ).length !== 1
      )
        throw new Error(
          "Initial image index is missing or duplicated in traffic audit",
        );
      const interactions = [];
      const input = page.getByLabel(
        locale === "en" ? "Search players" : "Spelers zoeken",
        { exact: true },
      );
      for (const q of ["a", "e", "i", "o", "n", "s", "t", "r", "an", "zzzz"]) {
        const expected = filterProfiles(
          index,
          { ...defaults, q },
          names,
        ).length.toLocaleString(locale);
        const start = performance.now();
        await input.fill(q);
        await page.waitForFunction(
          (expected) =>
            document
              .querySelector('[data-testid="player-result-count"]')
              ?.textContent?.startsWith(expected),
          expected,
        );
        interactions.push(performance.now() - start);
      }
      await input.fill("");
      await page.locator(".profile-list > li").nth(49).waitFor();
      await page.screenshot({
        path: `/private/tmp/fri-v11-${locale}-${width}.png`,
        fullPage: false,
      });
      const start = performance.now();
      await page.locator(".profile-name").first().click();
      await page.locator("#profile-detail .profile-metrics").first().waitFor();
      const visible = performance.now() - start;
      const resources = await page.evaluate(() =>
        performance
          .getEntriesByType("resource")
          .filter((e) => e.name.includes("/data/v11/profiles/"))
          .map((e) => ({
            duration_ms: e.responseEnd - e.startTime,
            transfer_bytes: e.transferSize,
            decoded_bytes: e.decodedBodySize,
          })),
      );
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      );
      rows.push({
        locale,
        width,
        initial_decoded_bytes: initial.reduce((n, r) => n + r.decoded, 0),
        initial_estimated_gzip_bytes: initial.reduce((n, r) => n + r.gzip, 0),
        initial_profile_requests: initial.filter((r) =>
          r.path.includes("/data/v11/profiles/"),
        ).length,
        index_gzip_bytes: initial.find((r) => r.path === "/data/v11/index.json")
          ?.gzip,
        interaction_p50_ms: quantile(interactions, 0.5),
        interaction_p95_ms: quantile(interactions, 0.95),
        profile_visible_ms: visible,
        profile_resources: resources,
        horizontal_overflow: overflow,
        initial_resources: initial,
      });
      if (
        overflow ||
        quantile(interactions, 0.5) >= 100 ||
        rows.at(-1).initial_profile_requests !== 0
      )
        throw new Error("Player database performance budget failed");
      await context.close();
    }
} finally {
  await browser.close();
}
const report = {
  environment: {
    platform: platform(),
    arch: arch(),
    cpu: cpus()[0].model,
    node: process.version,
    network:
      "localhost, unthrottled Chromium; gzip sizes estimated from decoded bodies",
    interaction_measurement:
      "Playwright fill-to-render wall clock, includes automation overhead; no CPU throttling",
  },
  profiles: index.profiles.length,
  index_bytes: readFileSync(new URL("artifacts/v12/public/index.json", root))
    .length,
  index_gzip_bytes: gzipSync(
    readFileSync(new URL("artifacts/v12/public/index.json", root)),
  ).length,
  pure_filter_p50_ms: quantile(timings, 0.5),
  pure_filter_p95_ms: quantile(timings, 0.95),
  browser: rows,
};
writeFileSync(
  new URL(
    imageAudit
      ? "artifacts/local-qa/player-images/search-performance.json"
      : "artifacts/v12/search-performance.json",
    root,
  ),
  JSON.stringify(report, null, 2) + "\n",
);
console.log(
  JSON.stringify(
    {
      ...report,
      browser: rows.map(({ initial_resources, ...r }) => ({
        ...r,
        initial_requests: initial_resources.length,
      })),
    },
    null,
    2,
  ),
);
