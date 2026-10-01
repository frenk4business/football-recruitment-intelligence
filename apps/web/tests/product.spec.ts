import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
for (const locale of ["en", "nl"] as const) {
  const nl = locale === "nl",
    base = nl ? "/nl" : "";
  test(`${locale}: home search, profile, similar comparison and language preserve context`, async ({
    page,
  }) => {
    await page.goto(`${base}/`);
    await page.locator("#home-query").fill("Alessia Russo");
    await page
      .getByRole("button", {
        name: nl ? "Spelers zoeken" : "Search players",
        exact: true,
      })
      .click();
    await expect(page.locator(".profile-name")).toHaveCount(1);
    await expect(page.locator("#profile-detail")).toHaveCount(0);
    await page.locator(".profile-name").click();
    await expect(page.locator("#profile-detail h2")).toHaveText(
      "Alessia Russo",
    );
    await expect(
      page.locator(".profile-style-bars").first().locator(":scope > div"),
    ).toHaveCount(8);
    await page.locator("#similar-players button").first().click();
    await expect(
      page.locator(".profile-metrics").first().locator("thead th"),
    ).toHaveCount(3);
    const before = new URL(page.url()).search;
    await page.locator("a.language").click();
    await expect(page.locator("html")).toHaveAttribute(
      "lang",
      nl ? "en" : "nl",
    );
    await expect(page.locator("#profile-detail h2")).toHaveText(
      "Alessia Russo",
    );
    expect(new URL(page.url()).search).toBe(before);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
  test(`${locale}: recruitment setup, shortlist, candidate details and advanced controls`, async ({
    page,
  }) => {
    await page.goto(`${base}/recruitment/`);
    await page
      .getByRole("combobox", {
        name: nl ? "Doelclub" : "Target club",
        exact: true,
      })
      .selectOption({ label: "Arsenal WFC" });
    await page
      .getByRole("combobox", {
        name: nl ? "Doelrol" : "Target role",
        exact: true,
      })
      .selectOption("CB");
    const feature = page.locator('[data-feature="progressive_passes_per90"]');
    await feature.locator("select").first().selectOption("minimum");
    await feature.locator("input[type=number]").fill("70");
    await page
      .getByRole("link", {
        name: nl ? "Kandidaten vinden →" : "Find candidates →",
        exact: true,
      })
      .click();
    await expect(page.locator(".recruitment-table tbody tr")).toHaveCount(10);
    await page.locator(".candidate-name").first().click();
    await expect(page.locator(".candidate-comparison")).toBeFocused();
    await expect(page.locator(".comparison-feature")).toHaveCount(1);
    await page
      .getByLabel(
        nl
          ? "Geavanceerde eisen · alle 18 kenmerken"
          : "Advanced requirements · all 18 features",
        { exact: true },
      )
      .check();
    await expect(page.locator(".requirement-row")).toHaveCount(18);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
  test(`${locale}: mobile menu, research methods and filter recovery`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`${base}/`);
    await page.locator(".mobile-menu > summary").click();
    await page
      .locator("#product-navigation")
      .getByRole("link", { name: nl ? "Onderzoek" : "Research", exact: true })
      .click();
    await expect(page.locator("h1")).toHaveText(
      nl ? "Onderzoek & methoden" : "Research & methods",
    );
    await page
      .locator(".research-links")
      .getByRole("link", {
        name: nl ? "Methodologie →" : "Methodology →",
        exact: true,
      })
      .click();
    await expect(page.locator(".research-toc")).toBeVisible();
    await page.goto(`${base}/players/?q=zzzzmissing`);
    await expect(page.locator(".profile-list li")).toHaveCount(0);
    await page
      .getByRole("button", {
        name: nl ? "Filters wissen" : "Clear filters",
        exact: true,
      })
      .click();
    await expect(page.locator(".profile-list li")).toHaveCount(50);
    await page.locator(".profile-name").first().click();
    await expect(page.locator("#profile-detail")).toBeFocused();
    await page
      .getByRole("button", {
        name: nl ? "Terug naar resultaten" : "Back to results",
        exact: true,
      })
      .click();
    await expect(page.locator(".profile-name").first()).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  });
}

test("native homepage search is allowed by CSP even without JavaScript", async ({
  browser,
  baseURL,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(baseURL + "/");
  await page.locator("#home-query").fill("Arsenal");
  await page
    .getByRole("button", { name: "Search players", exact: true })
    .click();
  await expect(page).toHaveURL(/players\/\?q=Arsenal/);
  await expect(page.locator("h1")).toHaveText("Player database");
  await context.close();
});

for (const locale of ["en", "nl"]) {
  test(`${locale}: mobile navigation works without JavaScript`, async ({
    browser,
    baseURL,
  }) => {
    const context = await browser.newContext({
      javaScriptEnabled: false,
      viewport: { width: 375, height: 812 },
    });
    const page = await context.newPage();
    await page.goto(baseURL + (locale === "nl" ? "/nl/" : "/"));
    const menu = page.locator(".mobile-menu > summary");
    await menu.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("#product-navigation")).toBeVisible();
    await expect(page.locator("#product-navigation a")).toHaveCount(3);
    await page
      .locator("#product-navigation")
      .getByRole("link", {
        name: locale === "nl" ? "Onderzoek" : "Research",
        exact: true,
      })
      .click();
    await expect(page.locator("h1")).toHaveText(
      locale === "nl" ? "Onderzoek & methoden" : "Research & methods",
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await context.close();
  });
}
