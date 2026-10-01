import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
import type { ProfileIndex } from "../src/lib/profile-contracts";
const index: ProfileIndex = JSON.parse(
  readFileSync(
    new URL("../../../artifacts/v11/public/index.json", import.meta.url),
    "utf8",
  ),
);
const a = index.profiles.find(
  (p) => p.provider === "statsbomb" && p.capabilities.common,
)!;
const b = index.profiles.find(
  (p) => p.provider === "wyscout" && p.capabilities.common,
)!;
const keeper = index.profiles.find(
  (p) => p.provider === "wyscout" && p.role_family === "GK",
)!;
for (const locale of ["en", "nl"] as const) {
  const route = locale === "en" ? "/players/" : "/nl/players/";
  const labels =
    locale === "en"
      ? {
          title: "Player database",
          search: "Player name",
          provider: "Provider",
          competition: "Competition",
          season: "Season",
          team: "Team",
          role: "Role",
          evidence: "Minimum reliable minutes",
          kind: "Profile type",
          clear: "Clear filters",
          next: "Next",
          previous: "Previous",
          compare: "Comparison",
          common: "Common cross-provider profile",
          error: "Try again",
        }
      : {
          title: "Spelersdatabase",
          search: "Spelersnaam",
          provider: "Provider",
          competition: "Competitie",
          season: "Seizoen",
          team: "Club",
          role: "Rol",
          evidence: "Minimaal betrouwbare minuten",
          kind: "Profieltype",
          clear: "Filters wissen",
          next: "Volgende",
          previous: "Vorige",
          compare: "Vergelijking",
          common: "Gedeeld profiel over providers heen",
          error: "Opnieuw proberen",
        };
  test(`${locale}: database fetches only the lean index, paginates and filters`, async ({
    page,
  }) => {
    const details: string[] = [];
    page.on("request", (r) => {
      if (r.url().includes("/data/v11/profiles/")) details.push(r.url());
    });
    await page.goto(route);
    await expect(page.locator("h1")).toHaveText(labels.title);
    await expect(page.locator(".profile-list > li")).toHaveCount(50);
    expect(details).toHaveLength(0);
    const first = await page.locator(".profile-name").first().textContent();
    await page.getByRole("button", { name: labels.next, exact: true }).click();
    await expect(page).toHaveURL(/page=2/);
    await expect(page.locator(".profile-name").first()).not.toHaveText(first!);
    await page
      .getByRole("button", { name: labels.previous, exact: true })
      .click();
    await page
      .getByLabel(labels.provider, { exact: true })
      .selectOption("wyscout");
    await page
      .getByLabel(labels.competition, { exact: true })
      .selectOption("premier-league");
    await page
      .getByLabel(labels.season, { exact: true })
      .selectOption("2017/2018");
    await page.getByLabel(labels.role, { exact: true }).selectOption("DEF");
    await page.getByLabel(labels.evidence, { exact: true }).selectOption("900");
    await page.getByLabel(labels.kind, { exact: true }).selectOption("common");
    await expect(page.locator(".profile-list > li").first()).toContainText(
      "Pappalardo / Wyscout",
    );
    const count = await page.getByTestId("player-result-count").textContent();
    await page.reload();
    await expect(page.getByTestId("player-result-count")).toHaveText(count!);
    await expect(page.getByLabel(labels.provider, { exact: true })).toHaveValue(
      "wyscout",
    );
    await page.getByRole("button", { name: labels.clear, exact: true }).click();
    await page
      .getByLabel(labels.search, { exact: true })
      .fill("zzzz_no_such_player");
    await expect(page.locator(".profile-list > li")).toHaveCount(0);
  });
  test(`${locale}: lazy detail and cross-provider comparison use common metrics only`, async ({
    page,
  }) => {
    await page.goto(`${route}?profile=${a.id}&compare=${b.id}`);
    const detail = page.locator("#profile-detail");
    await expect(
      detail.locator(".profile-metrics").first().locator("tbody tr"),
    ).toHaveCount(3);
    await expect(detail).toContainText(a.name);
    await expect(detail).toContainText(b.name);
    await expect(detail).toContainText("StatsBomb");
    await expect(detail).toContainText("Pappalardo / Wyscout");
    await expect(
      detail.locator(".profile-metrics").first().locator("thead th"),
    ).toHaveCount(3);
    await detail.locator(".native-details summary").first().click();
    await expect(detail.locator(".native-details thead th")).toHaveCount(2);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
  test(`${locale}: unsupported comparison fails closed`, async ({ page }) => {
    await page.goto(`${route}?profile=${a.id}&compare=${keeper.id}`);
    await expect(page.locator("#profile-detail")).toContainText(
      locale === "en"
        ? "These profiles do not share"
        : "Deze profielen delen geen",
    );
    await expect(page.locator("#profile-detail > .table-wrap")).toHaveCount(0);
  });
  test(`${locale}: mobile keyboard, detail focus and responsive layout`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(route);
    await expect(page.locator(".profile-list > li")).toHaveCount(50);
    await page.getByLabel(labels.search, { exact: true }).fill(a.name);
    const open = page.locator(".profile-name").first();
    await open.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("#profile-detail")).toBeFocused();
    await expect(
      page.locator("#profile-detail .profile-metrics").first(),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
  test(`${locale}: network and integrity failures are recoverable`, async ({
    page,
  }) => {
    await page.route("**/data/v11/index.json*", (r) =>
      r.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
    );
    await page.goto(route);
    await expect(page.locator("main").getByRole("alert")).toBeVisible();
    await page.unroute("**/data/v11/index.json*");
    await page.getByRole("button", { name: labels.error, exact: true }).click();
    await expect(page.locator(".profile-list > li")).toHaveCount(50);
    await page.route("**/data/v11/profiles/**", (r) =>
      r.fulfill({
        status: 200,
        contentType: "application/json",
        body: '{"version":"wrong"}',
      }),
    );
    await page.locator(".profile-name").first().click();
    await expect(page.locator("main").getByRole("alert")).toBeVisible();
    await expect(page.locator("#profile-detail .profile-metrics")).toHaveCount(
      0,
    );
  });
}
