import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
for (const locale of ["en", "nl"]) {
  const nl = locale === "nl",
    base = nl ? "/nl" : "";
  test(`${locale}: global search groups real players, teams and competitions without detail fetches`, async ({
    page,
  }) => {
    const details: string[] = [];
    page.on("request", (r) => {
      if (r.url().includes("/data/v11/profiles/")) details.push(r.url());
    });
    await page.goto(`${base}/`);
    await page.locator("#home-query").fill("Arsenal");
    await expect(page.locator(".global-search-results h2")).toHaveCount(2);
    expect(details).toHaveLength(0);
    await page.locator("#home-query").fill("Premier League");
    await expect(
      page.locator(".global-search-results").getByRole("heading", {
        name: nl ? "Competities" : "Competitions",
        exact: true,
      }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.locator(".global-search-results")).toHaveCount(0);
    await page.locator("#home-query").fill("Alessia Russo");
    await page.locator(".global-search-results li a").first().click();
    await expect(page.locator("#profile-detail h2")).toHaveText(
      "Alessia Russo",
    );
    await expect(page.locator(".profile-metrics").first()).toBeVisible();
    expect(details).toHaveLength(1);
  });
  test(`${locale}: three-player comparison survives language and browser history on mobile`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`${base}/players/?q=Alessia+Russo`);
    await page.locator(".profile-name").first().click();
    await page.locator("#similar-players button").nth(0).click();
    await page.locator("#similar-players button").nth(1).click();
    await expect(
      page.locator(".profile-metrics").first().locator("thead th"),
    ).toHaveCount(4);
    const query = new URL(page.url()).search;
    await expect(page.locator(".comparison-member")).toHaveCount(2);
    await page.goBack();
    await expect(
      page.locator(".profile-metrics").first().locator("thead th"),
    ).toHaveCount(3);
    await page.goForward();
    await expect(
      page.locator(".profile-metrics").first().locator("thead th"),
    ).toHaveCount(4);
    await page.locator("a.language").click();
    await expect(page.locator("html")).toHaveAttribute(
      "lang",
      nl ? "en" : "nl",
    );
    await expect(
      page.locator(".profile-metrics").first().locator("thead th"),
    ).toHaveCount(4);
    expect(new URL(page.url()).search).toBe(query);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
  test(`${locale}: simple and advanced recruitment preserve rankings and restore scenarios`, async ({
    page,
  }) => {
    await page.goto(`${base}/recruitment/`);
    const feature = page.locator('[data-feature="progressive_passes_per90"]');
    await feature.locator("select").first().selectOption("minimum");
    await feature.locator('input[type="number"]').fill("70");
    await expect(feature.locator(".hard-constraint")).toBeHidden();
    const query = new URL(page.url()).search;
    const rows = () =>
      page
        .locator(".recruitment-table tbody tr")
        .evaluateAll((rs) => rs.map((r) => r.textContent));
    await expect(page.locator(".recruitment-table tbody tr")).toHaveCount(10);
    const before = await rows();
    await page
      .getByLabel(
        nl
          ? "Geavanceerde eisen · alle 18 kenmerken"
          : "Advanced requirements · all 18 features",
        { exact: true },
      )
      .check();
    expect(await rows()).toEqual(before);
    expect(new URL(page.url()).search).toBe(query);
    await feature.locator("select").first().selectOption("maximum");
    await page.goBack();
    await expect(feature.locator("select").first()).toHaveValue("minimum");
    expect(await rows()).toEqual(before);
    await page.goForward();
    await expect(feature.locator("select").first()).toHaveValue("maximum");
  });
}
