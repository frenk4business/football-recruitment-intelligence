import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { writeFileSync, mkdirSync } from "node:fs";
const phase = process.argv[2] ?? "after";
const dir = fileURLToPath(
  new URL("../../../artifacts/local-qa/ui-redesign/", import.meta.url),
);
mkdirSync(dir, { recursive: true });
const browser = await chromium.launch();
const report = [];
for (const locale of ["en", "nl"])
  for (const width of [1440, 375])
    for (const route of [
      "",
      "players/",
      "recruitment/",
      "translation/",
      "methodology/",
      ...(phase === "after" ? ["research/"] : []),
    ]) {
      const page = await browser.newPage({ viewport: { width, height: 960 } });
      await page.addInitScript(() => {
        window.lcp = 0;
        new PerformanceObserver((l) => {
          window.lcp = l.getEntries().at(-1).startTime;
        }).observe({ type: "largest-contentful-paint", buffered: true });
      });
      await page.goto(
        (process.env.PREVIEW_URL ?? "http://127.0.0.1:4173") +
          "/" +
          (locale === "nl" ? "nl/" : "") +
          route,
      );
      await page.waitForTimeout(350);
      const row = { locale, width, route };
      row.initial = await page.evaluate(() => ({
        lcp: window.lcp,
        js: performance
          .getEntriesByType("resource")
          .filter((r) => new URL(r.name).pathname.endsWith(".js"))
          .reduce((a, r) => a + r.decodedBodySize, 0),
        json: performance
          .getEntriesByType("resource")
          .filter((r) => r.name.includes(".json"))
          .reduce((a, r) => a + r.decodedBodySize, 0),
      }));
      if (route === "players/") {
        await page.locator(".profile-name").first().waitFor();
        const t = performance.now();
        await page.locator("input[type=search]").fill("Hemp");
        await page.waitForFunction(() =>
          document.querySelector(".profile-name")?.textContent.includes("Hemp"),
        );
        row.search_ms = performance.now() - t;
        await page.locator("input[type=search]").fill("");
      }
      if (route === "recruitment/") {
        const t = performance.now();
        await page
          .locator('[data-feature="progressive_passes_per90"] select')
          .first()
          .selectOption("minimum");
        await page.locator(".recruitment-table tbody tr").first().waitFor();
        row.recruitment_ms = performance.now() - t;
      }
      await page.screenshot({
        path: `${dir}/${phase}-${locale}-${width}-${route.replace("/", "") || "home"}.png`,
      });
      if (route === "players/") {
        await page.locator(".profile-name").first().click();
        await page.locator(".profile-metrics").first().waitFor();
        await page.screenshot({
          path: `${dir}/${phase}-${locale}-${width}-profile.png`,
        });
      }
      row.overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      );
      report.push(row);
      await page.close();
    }
await browser.close();
writeFileSync(`${dir}/${phase}.json`, JSON.stringify(report, null, 2));
console.log(report);
