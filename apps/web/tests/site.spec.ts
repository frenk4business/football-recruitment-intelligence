import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
for (const locale of ["en", "nl"]) {
  const base = locale === "en" ? "" : "/nl";
  test(`${locale}: pages, language, accessibility and assets`, async ({
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
    for (const section of [
      "",
      "explorer/",
      "player-dna/",
      "coverage/",
      "methodology/",
      "roadmap/",
    ]) {
      const response = await page.goto(`${base}/${section}`);
      expect(response?.status()).toBe(200);
      await expect(page.locator("html")).toHaveAttribute("lang", locale);
      await expect(page.locator("h1")).toHaveCount(1);
      if (section === "explorer/")
        await expect(
          page.getByRole("heading", { name: /Argentina/ }),
        ).toBeVisible();
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze();
      expect(results.violations).toEqual([]);
    }
    expect(errors).toEqual([]);
  });
}
test("explorer controls, tracking slider, empty result and mobile overflow", async ({
  page,
}) => {
  await page.goto("/explorer/");
  await expect(page.getByRole("heading", { name: /Argentina/ })).toBeVisible();
  await page.getByLabel("Find a player").fill("zzzzmissing");
  await expect(page.getByText("No players match these filters.")).toBeVisible();
  await page.getByLabel("Source", { exact: true }).selectOption("skillcorner");
  await expect(
    page.getByRole("heading", { name: /Western United/ }),
  ).toBeVisible();
  await page.getByRole("slider").fill("30");
  await expect(page.locator(".time-control")).toContainText("30 s");
  await page
    .getByRole("link", { name: "Taal wijzigen naar Nederlands" })
    .click();
  await expect(page).toHaveURL(/\/nl\/explorer\//);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator("html")).toHaveAttribute("lang", "nl");
  await expect(page.getByRole("heading", { name: /Argentina/ })).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    )
    .toBeTruthy();
  await page.screenshot({
    path: "../../artifacts/local-qa/mobile-explorer.png",
    fullPage: true,
  });
});
test("failed data requests have a retry state", async ({ page }) => {
  await page.route("**/data/explorer/*.json", (r) => r.abort());
  await page.goto("/explorer/");
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "could not be loaded",
  );
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
});
test("desktop overview evidence screenshot", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await page.screenshot({
    path: "../../artifacts/local-qa/desktop-overview.png",
    fullPage: true,
  });
});
