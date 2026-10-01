import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const locale of ["en", "nl"]) {
  test(`${locale}: translation scenario, uncertainty, evidence and accessibility`, async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => {
      if (m.type() === "error") errors.push(m.text());
    });
    page.on("response", (r) => {
      if (r.status() >= 400) errors.push(`${r.status()}: ${r.url()}`);
    });
    await page.goto(locale === "en" ? "/translation/" : "/nl/translation/");
    await expect(
      page.locator(".translation-results .translation-metric"),
    ).toHaveCount(4);
    await expect(page.locator(".translation-evidence dl > div")).toHaveCount(4);
    await expect(page.locator(".translation-results")).toContainText("80%");
    await page
      .locator(".translation-scenario select")
      .nth(1)
      .selectOption({ index: 0 });
    await expect(
      page.locator(".translation-results .translation-range svg"),
    ).toHaveCount(4);
    await page.locator(".translation-research summary").focus();
    await page.keyboard.press("Enter");
    await expect(
      page.locator(".translation-research svg").first(),
    ).toBeVisible();
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    expect(result.violations).toEqual([]);
    await page.locator(".translation-limits summary").click();
    await page.locator(".translation-limits a").click();
    await expect(page).toHaveURL(/methodology\/#translation/);
    await expect(page.locator(".translation-calibration > div")).toHaveCount(4);
    expect(errors).toEqual([]);
  });
}

test("translation withholds unsupported roles/seasons, empty search and mobile", async ({
  page,
}) => {
  await page.goto("/translation/");
  await expect(page.locator(".translation-results")).toBeVisible();
  await page
    .getByLabel("Assumed target role", { exact: true })
    .selectOption("AM");
  await expect(page.locator(".translation-unavailable")).toContainText(
    "No supported estimate",
  );
  await expect(page.locator(".translation-results")).toHaveCount(0);
  const index = await (
    await page.request.get("/data/phase3/index.json")
  ).json();
  const player = index.players.find(
    (p: { supported_sources: number }) => p.supported_sources === 0,
  );
  await page.getByLabel("Find a player", { exact: true }).fill(player.name);
  await expect(page.locator(".translation-unavailable")).toBeVisible();
  await page
    .getByLabel("Find a player", { exact: true })
    .fill("zzzznonexistent");
  await expect(page.locator(".state")).toContainText("No players");
  await page.getByLabel("Find a player", { exact: true }).fill("");
  await expect(page.locator(".translation-results")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    )
    .toBeTruthy();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: "../../artifacts/local-qa/mobile-translation.png",
    fullPage: true,
  });
});

test("translation data failure retries and loads one player lazily", async ({
  page,
}) => {
  await page.route("**/data/phase3/players/*.json*", (r) => r.abort());
  await page.goto("/translation/");
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "could not be loaded",
  );
  await page.unroute("**/data/phase3/players/*.json*");
  const requests: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/data/phase3/players/")) requests.push(r.url());
  });
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.locator(".translation-results")).toBeVisible();
  expect(requests).toHaveLength(1);
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.screenshot({
    path: "../../artifacts/local-qa/desktop-translation.png",
    fullPage: true,
  });
});
