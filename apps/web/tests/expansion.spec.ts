import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
for (const locale of ["en", "nl"]) {
  const base = locale === "en" ? "" : "/nl";
  const en = locale === "en";
  test(`${locale}: five native leagues, scenario reset, own-league default, wider discovery and sharing`, async ({
    page,
  }) => {
    const requests: string[] = [];
    const errors: string[] = [];
    page.on("request", (r) => requests.push(r.url()));
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(`${base}/recruitment/`);
    await expect(page.locator(".native-results > li")).toHaveCount(30);
    expect(
      requests.filter((u) => /\/data\/v12\/recruitment\/wyscout-/.test(u)),
    ).toHaveLength(1);
    expect(requests.some((u) => u.includes("/data/phase4/"))).toBe(false);
    const competition = page.getByRole("combobox", {
      name: en ? "Competition" : "Competitie",
      exact: true,
    });
    const values = await competition
      .locator("option")
      .evaluateAll((nodes) => nodes.map((n) => (n as HTMLOptionElement).value));
    expect(values).toHaveLength(5);
    for (const value of values) {
      await competition.selectOption(value);
      await expect(page.locator(".native-results > li")).toHaveCount(30);
      await expect(
        page.getByLabel(
          en
            ? "Include players from other Wyscout leagues"
            : "Neem spelers uit andere Wyscout-competities mee",
        ),
      ).not.toBeChecked();
      await expect(
        page
          .getByRole("combobox", { name: en ? "Role" : "Rol", exact: true })
          .locator("option"),
      ).toHaveCount(3);
    }
    await page
      .getByRole("button", {
        name: en ? "Add requirement" : "Criterium toevoegen",
        exact: true,
      })
      .click();
    await expect(page.locator(".native-requirement")).toHaveCount(1);
    await page
      .getByLabel(en ? "Target value" : "Doelwaarde", { exact: true })
      .fill("1.5");
    await page
      .getByLabel(
        en
          ? "Include players from other Wyscout leagues"
          : "Neem spelers uit andere Wyscout-competities mee",
      )
      .check();
    await expect(page.locator(".native-recruitment .notice")).toContainText(
      en ? "No league-performance translation" : "geen competitievertaling",
    );
    await page
      .getByRole("button", {
        name: en ? "Share scenario" : "Scenario delen",
        exact: true,
      })
      .click();
    const url = await page
      .getByLabel(en ? "Share URL" : "Deellink", { exact: true })
      .inputValue();
    await page.goto(url);
    await expect(page.locator(".native-requirement")).toHaveCount(1);
    await expect(
      page.getByLabel(en ? "Target value" : "Doelwaarde", { exact: true }),
    ).toHaveValue("1.5");
    await expect(page.locator(".native-results > li")).toHaveCount(30);
    await page.locator(".native-results .profile-name").first().click();
    await expect(
      page.getByRole("region", {
        name: en ? "Candidate evidence" : "Onderbouwing kandidaat",
      }),
    ).toBeVisible();
    await page.setViewportSize({ width: 375, height: 812 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      path: `../../artifacts/local-qa/v12-recruitment-${locale}.png`,
      fullPage: true,
    });
    await competition.selectOption(values[0]);
    await expect(page.locator(".native-requirement")).toHaveCount(0);
    await page
      .getByRole("combobox", { name: "Dataset / provider", exact: true })
      .selectOption("wsl");
    await expect(page.locator(".recruitment-empty")).toBeVisible();
    expect(errors).toEqual([]);
  });
  test(`${locale}: metadata-only clubs, player metadata and physical aggregates remain separate`, async ({
    page,
  }) => {
    await page.goto(`${base}/players/`);
    await expect(page.locator(".profile-list > li")).toHaveCount(50);
    await page
      .getByRole("button", {
        name: en ? "Club directory" : "Clubdirectory",
        exact: true,
      })
      .click();
    await page
      .getByLabel(en ? "Search metadata" : "Metadata zoeken", { exact: true })
      .fill("Ajax");
    await page
      .locator(".directory-list")
      .getByRole("button", { name: "Ajax Amsterdam", exact: true })
      .click();
    await expect(
      page.locator(".discovery-panel .profile-detail .notice"),
    ).toContainText(
      en ? "cannot be a recruitment target" : "geen recruitmentdoel",
    );
    const fixture = page.getByRole("combobox", {
      name: en ? "Fixture source / season" : "Wedstrijdbron / seizoen",
      exact: true,
    });
    await fixture.selectOption({ index: 1 });
    await expect(
      page.locator(".discovery-panel table tbody tr").first(),
    ).toBeVisible();
    await page
      .getByRole("button", {
        name: en ? "Player metadata" : "Spelersmetadata",
        exact: true,
      })
      .click();
    await expect(
      page.locator(".discovery-panel table tbody tr").first(),
    ).toBeVisible();
    await expect(page.locator(".discovery-panel")).toContainText(
      en ? "No global person merge" : "Geen globale persoonskoppeling",
    );
    await page
      .getByRole("button", {
        name: en ? "Physical research" : "Fysiek onderzoek",
        exact: true,
      })
      .click();
    await expect(page.locator(".discovery-panel")).toContainText("290");
    await page.locator(".directory-list button").first().click();
    await expect(
      page.locator(".discovery-panel details").first(),
    ).toBeVisible();
    await page
      .locator(".discovery-panel details")
      .first()
      .locator("summary")
      .click();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  });
}
test("native artifacts reject tampering and load no fabricated shortlist", async ({
  page,
}) => {
  await page.route("**/data/v12/recruitment/wyscout-*.json*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: "{}" }),
  );
  await page.goto("/recruitment/");
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "Data could not be loaded.",
  );
  await expect(page.locator(".native-results")).toHaveCount(0);
  await page.unroute("**/data/v12/recruitment/wyscout-*.json*");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.locator(".native-results > li")).toHaveCount(30);
});
