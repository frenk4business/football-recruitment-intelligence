import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
for (const locale of ["en", "nl"] as const) {
  const route = locale === "en" ? "/players/" : "/nl/players/";
  test(`${locale}: optional images fail closed without affecting analytics`, async ({
    page,
  }) => {
    const external: string[] = [];
    page.on("request", (request) => {
      if (/wikimedia\.org|wikidata\.org/.test(request.url()))
        external.push(request.url());
    });
    await page.route("**/players/images/index-*.json", (r) =>
      r.fulfill({ status: 503, body: "unavailable" }),
    );
    await page.goto(route);
    const rows = page.locator(".profile-list > li");
    await expect(rows).toHaveCount(50);
    const avatar = rows.first().locator(".player-avatar");
    await expect(avatar).toHaveAttribute("aria-hidden", "true");
    await expect(avatar).not.toBeEmpty();
    expect((await avatar.boundingBox())!.width).toBe(32);
    await rows.first().locator(".profile-name").click();
    await expect(page.locator("#profile-detail .avatar-large")).toHaveAttribute(
      "role",
      "img",
    );
    await expect(page.locator("#profile-detail .avatar-large")).toHaveAttribute(
      "aria-label",
      /No verified player photo available|Geen geverifieerde spelersfoto beschikbaar/,
    );
    await expect(page.locator(".profile-metrics").first()).toBeVisible();
    await expect(
      page.locator(".profile-metrics .avatar-medium").first(),
    ).toBeVisible();
    expect(external).toEqual([]);
    await page.setViewportSize({ width: 375, height: 812 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const audit = await new AxeBuilder({ page }).analyze();
    expect(audit.violations).toEqual([]);
  });
  test(`${locale}: photo requests stay local and credits remain reachable`, async ({
    page,
  }) => {
    const remote: string[] = [];
    page.on("request", (request) => {
      if (/wikimedia\.org|wikidata\.org/.test(request.url()))
        remote.push(request.url());
    });
    await page.goto(route);
    await expect(page.locator(".profile-list > li")).toHaveCount(50);
    await page.locator(".profile-name").first().click();
    await page.locator("#profile-quality > summary").click();
    await expect(page.locator(".photo-attribution").first()).toBeVisible();
    await page
      .getByRole("link", {
        name: locale === "en" ? "Image credits" : "Afbeeldingscredits",
        exact: true,
      })
      .click();
    await expect(page.locator("#image-credits")).toBeVisible();
    await page
      .getByRole("link", {
        name:
          locale === "en"
            ? "All photo sources and licences"
            : "Alle fotobronnen en licenties",
      })
      .click();
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(page.locator(".credits > li").first()).toBeVisible();
    await page.setViewportSize({ width: 375, height: 812 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    expect(remote).toEqual([]);
  });
}

for (const locale of ["en", "nl"] as const) {
  for (const broken of [false, true]) {
    test(`${locale}: approved photo ${broken ? "falls back on image error" : "loads with stable dimensions and attribution"}`, async ({
      page,
    }) => {
      let failedImages = 0;
      if (broken)
        await page.route("**/players/images/*.webp", (route) => {
          failedImages += 1;
          return route.abort();
        });
      await page.goto(
        `${locale === "en" ? "" : "/nl"}/players/?q=Alessia+Russo`,
      );
      await page.locator(".profile-name").first().click();
      const avatar = page.locator("#profile-detail .avatar-large");
      if (broken) {
        await expect.poll(() => failedImages).toBeGreaterThan(0);
        await expect(avatar).toHaveAttribute(
          "aria-label",
          /No verified player photo available|Geen geverifieerde spelersfoto beschikbaar/,
        );
        await expect(avatar.locator("img")).toHaveCount(0);
      } else {
        await expect(avatar.locator("img")).toBeVisible();
        await expect(avatar.locator("img")).toHaveJSProperty(
          "naturalWidth",
          256,
        );
      }
      expect((await avatar.boundingBox())!.width).toBe(96);
      expect((await avatar.boundingBox())!.height).toBe(96);
      await page.locator("#profile-quality > summary").click();
      await expect(
        page
          .locator(".photo-attribution")
          .first()
          .getByRole("link", { name: "Wikimedia Commons" }),
      ).toBeVisible();
      await expect(page.locator(".profile-metrics").first()).toBeVisible();
    });
  }
}
