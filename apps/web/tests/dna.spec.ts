import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
for (const locale of ["en", "nl"]) {
  test(`${locale}: Player DNA selection, comparison, keyboard, map and accessibility`, async ({
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
    await page.goto(locale === "en" ? "/player-dna/" : "/nl/player-dna/");
    await expect(page.locator(".dna-header h2")).toBeVisible();
    await expect(page.locator(".dna-neighbors tbody tr")).toHaveCount(10);
    await page.locator(".dna-neighbors button").first().focus();
    await page.keyboard.press("Enter");
    await expect(page.locator(".dna-comparison")).toBeVisible();
    await expect(page.locator(".dna-comparison tbody tr")).toHaveCount(10);
    await page.locator(".dna-secondary-grid button").first().click();
    await expect(page.locator(".dna-map")).toBeVisible();
    await page.locator(".dna-map g").first().focus();
    await page.keyboard.press("Enter");
    await expect(page.locator(".dna-header h2")).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    expect(results.violations).toEqual([]);
    await page.locator(".dna-header a").click();
    await expect(page).toHaveURL(/methodology\/#player-dna/);
    expect(errors).toEqual([]);
  });
}
test("Player DNA evidence thresholds, unavailable values, empty search and mobile", async ({
  page,
}) => {
  await page.goto("/player-dna/");
  await expect(page.locator(".dna-header h2")).toBeVisible();
  const index = await (
    await page.request.get("/data/phase2/index.json")
  ).json();
  const low = index.players.find(
    (p: {
      minutes: number;
      primary_role: string;
      eligibility: Record<string, string[]>;
    }) =>
      p.minutes >= 450 && p.minutes < 900 && p.eligibility["450"].length === 0,
  );
  await page.getByLabel("Find a player", { exact: true }).fill(low.name);
  await expect(page.locator(".dna-ineligible")).toContainText("does not meet");
  await expect(page.locator(".dna-neighbors tbody tr")).toHaveCount(0);
  await page
    .getByLabel("Minimum reliable minutes", { exact: true })
    .selectOption("450");
  await expect(page.locator(".dna-neighbors tbody tr")).toHaveCount(10);
  const unused = index.players.find(
    (p: { minutes: number }) => p.minutes === 0,
  );
  await page.getByLabel("Find a player", { exact: true }).fill(unused.name);
  await expect(page.locator(".dna-profile")).toContainText("Not available");
  await page.getByLabel("Find a player", { exact: true }).fill("zzzzmissing");
  await expect(page.locator(".state")).toContainText("No players");
  await page.getByLabel("Find a player", { exact: true }).fill("");
  await page
    .getByLabel("Minimum reliable minutes", { exact: true })
    .selectOption("900");
  await expect(page.locator(".dna-header h2")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    )
    .toBeTruthy();
  await page.screenshot({
    path: "../../artifacts/local-qa/mobile-player-dna.png",
    fullPage: true,
  });
});
test("Player DNA failed data request can retry", async ({ page }) => {
  await page.route("**/data/phase2/900/*.json", (r) => r.abort());
  await page.goto("/player-dna/");
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "could not be loaded",
  );
  await page.unroute("**/data/phase2/900/*.json");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.locator(".dna-header h2")).toBeVisible();
});
test("Player DNA desktop design review and initial request budget", async ({
  page,
}) => {
  const data: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/data/phase2/")) data.push(r.url());
  });
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page.goto("/player-dna/");
  await expect(page.locator(".dna-neighbors tbody tr")).toHaveCount(10);
  expect(data.filter((url) => /\/900\//.test(url))).toHaveLength(1);
  expect(data.some((url) => url.includes("map-"))).toBeFalsy();
  await page.screenshot({
    path: "../../artifacts/local-qa/desktop-player-dna.png",
    fullPage: true,
  });
});
