import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const locale of ["en", "nl"] as const) {
  const nl = locale === "nl",
    base = nl ? "/nl" : "";
  test(`${locale}: recruitment requirements, replacements, context, evidence and accessibility`, async ({
    page,
  }) => {
    const errors: string[] = [],
      requests: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => {
      if (m.type() === "error") errors.push(m.text());
    });
    page.on("response", (r) => {
      if (r.status() >= 400) errors.push(`${r.status()}: ${r.url()}`);
    });
    page.on("request", (r) => {
      if (r.url().includes("/data/phase4/")) requests.push(r.url());
    });
    await page.goto(`${base}/recruitment/?dataset=wsl`);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(page.locator(".recruitment-empty")).toContainText(
      nl ? "Kies een eis" : "Choose a requirement",
    );
    const progressive = page.locator(
      '[data-feature="progressive_passes_per90"]',
    );
    await progressive.locator("select").first().selectOption("minimum");
    await expect(page.locator(".recruitment-table tbody tr")).toHaveCount(10);
    await expect(page.locator(".recruitment-translation")).toContainText(
      nl ? "geen gevalideerd vertaalmodel" : "No validated translation model",
    );
    await expect(page.locator(".recruitment-table")).toContainText(
      nl ? "Stabiliteit van buren" : "Neighbour stability",
    );
    await expect(page.locator(".recruitment-table")).toContainText(
      nl ? "Grootste afwijking" : "Main mismatch",
    );
    const checkboxes = page.locator(
      '.recruitment-table input[type="checkbox"]',
    );
    for (let i = 0; i < 3; i++) await checkboxes.nth(i).check();
    await expect(checkboxes.nth(3)).toBeDisabled();
    await expect(page.locator(".comparison-grid article")).toHaveCount(3);
    await expect(page.locator(".comparison-grid")).toContainText(
      nl ? "Aandeel in afwijking" : "Share of mismatch",
    );
    expect(requests.filter((u) => u.includes("bootstrap"))).toHaveLength(0);
    await page.locator(".robustness-panel summary").click();
    await expect(page.locator(".robustness-panel tbody tr")).toHaveCount(10);
    await expect(
      page.locator(".robustness-panel tbody tr").first(),
    ).toContainText("%");
    await expect
      .poll(() => requests.filter((u) => u.includes("bootstrap")).length)
      .toBe(1);
    await expect(page.locator(".robustness-panel")).toContainText(
      nl ? "Steekproeven van profielen" : "Profile sampling",
    );
    await page
      .getByRole("button", {
        name: nl ? "Speler vervangen" : "Replace a Player",
        exact: false,
      })
      .click();
    await expect(
      page.getByRole("combobox", {
        name: nl ? "Referentiespeler" : "Reference player",
        exact: true,
      }),
    ).toBeEnabled();
    await expect(page.locator(".requirement-row.is-active")).toHaveCount(18);
    const reference = await page
      .getByRole("combobox", {
        name: nl ? "Referentiespeler" : "Reference player",
        exact: true,
      })
      .inputValue();
    await expect(
      page.locator(`.recruitment-table [data-player="${reference}"]`),
    ).toHaveCount(0);
    await page.locator(".requirements-disclosure > summary").click();
    await page
      .getByLabel(
        nl
          ? "Geavanceerde eisen · alle 18 kenmerken"
          : "Advanced requirements · all 18 features",
        { exact: true },
      )
      .check();
    await progressive.locator("select").first().selectOption("maximum");
    await progressive.locator('input[type="number"]').fill("40");
    await expect(progressive).toContainText(nl ? "Jouw keuze" : "Your choice");
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
    await expect(page.locator(".recruitment-table tbody tr")).toHaveCount(10);
    await page
      .getByRole("button", {
        name: nl ? "Clubcontext" : "Club Context",
        exact: false,
      })
      .click();
    await expect(page.locator(".club-context h2")).toHaveText("Arsenal WFC");
    await expect(page.locator(".team-feature-grid article")).toHaveCount(14);
    await expect(page.locator(".club-context")).toContainText(
      nl ? "werkelijke wedstrijdminuten" : "actual match minutes",
    );
    await page.locator(".team-feature-grid button").first().click();
    await expect(page.locator(".requirement-row.is-active")).toContainText([
      nl ? "Overgenomen clubkenmerk" : "Adopted club characteristic",
    ]);
    const axe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    expect(axe.violations).toEqual([]);
    expect(errors).toEqual([]);
  });
}
test("recruitment sharing, locale switch, reset, strict URLs and hard exclusions", async ({
  page,
}) => {
  await page.goto("/recruitment/?dataset=wsl");
  const feature = page.locator('[data-feature="progressive_passes_per90"]');
  await feature.locator("select").first().selectOption("minimum");
  await feature.locator('input[type="number"]').fill("100");
  await page
    .getByLabel("Advanced requirements · all 18 features", { exact: true })
    .check();
  await feature.getByRole("checkbox").check();
  await expect(page.locator(".recruitment-empty")).toContainText(
    "No candidates",
  );
  await feature.getByRole("checkbox").uncheck();
  const ids = await page
    .locator(".recruitment-table tbody tr")
    .evaluateAll((rows) => rows.map((r) => r.getAttribute("data-player")));
  await page
    .getByRole("button", { name: "Copy scenario link", exact: false })
    .click();
  const url = await page
    .getByLabel("Copy this scenario link", { exact: true })
    .inputValue();
  await page.goto(url);
  await expect(page.locator(".recruitment-table tbody tr")).toHaveCount(10);
  expect(
    await page
      .locator(".recruitment-table tbody tr")
      .evaluateAll((rows) => rows.map((r) => r.getAttribute("data-player"))),
  ).toEqual(ids);
  await page.locator("a.language").click();
  await expect(page.locator("html")).toHaveAttribute("lang", "nl");
  await expect(
    page.locator(
      '[data-feature="progressive_passes_per90"] input[type="number"]',
    ),
  ).toHaveValue("100");
  await page
    .getByRole("button", { name: "Scenario herstellen", exact: true })
    .click();
  await expect(page.locator(".recruitment-empty")).toContainText(
    "Kies een eis",
  );
  await page.goto("/recruitment/?v=999&role=GK");
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "shared scenario is invalid",
  );
  await expect(
    page
      .getByRole("combobox", { name: "Target role", exact: true })
      .locator('option[value="AM"]'),
  ).toHaveCount(0);
  // Existing shared URLs for unsupported roles remain readable and fail closed.
  const unsupported = new URL(page.url());
  unsupported.searchParams.set("role", "AM");
  await page.goto(unsupported.href);
  await expect(
    page.getByRole("combobox", { name: "Target role", exact: true }),
  ).toHaveValue("AM");
  await page
    .locator('[data-feature="pressures_per90"] select')
    .first()
    .selectOption("minimum");
  await expect(page.locator(".recruitment-empty")).toContainText(
    "No candidates",
  );
});
test("recruitment failed artifacts retry and do not invent profiles", async ({
  page,
}) => {
  await page.route("**/data/phase4/index.json*", (r) => r.abort());
  await page.goto("/recruitment/?dataset=wsl");
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "could not be loaded",
  );
  await expect(page.locator(".recruitment-table")).toHaveCount(0);
  await page.unroute("**/data/phase4/index.json*");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  // Club context is a separate request that inserts content above the panel.
  await expect(page.locator(".club-summary")).toBeVisible();
  await page
    .locator('[data-feature="pressures_per90"] select')
    .first()
    .selectOption("minimum");
  await page.route("**/data/phase4/bootstrap/*.json*", (r) => r.abort());
  await page.locator(".robustness-panel summary").click();
  await expect(
    page.locator(".robustness-panel").getByRole("alert"),
  ).toContainText("Profile sensitivity is unavailable");
  await expect(page.locator(".recruitment-table tbody tr")).toHaveCount(10);
  await page.unroute("**/data/phase4/bootstrap/*.json*");
  await page
    .locator(".robustness-panel")
    .getByRole("button", { name: "Try again" })
    .click();
  await expect(
    page.locator(".robustness-panel").getByRole("alert"),
  ).toHaveCount(0);
  await expect(
    page.locator(".robustness-panel tbody tr").first().locator("td").last(),
  ).toContainText("%");
});
test("recruitment mobile and keyboard workflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/nl/recruitment/?dataset=wsl");
  const replace = page.getByRole("button", {
    name: "Speler vervangen",
    exact: false,
  });
  await replace.focus();
  await expect(replace).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator(".recruitment-table tbody tr")).toHaveCount(10);
  const comparison = page
    .locator('.recruitment-table input[type="checkbox"]')
    .first();
  await comparison.focus();
  await page.keyboard.press("Space");
  await expect(page.locator(".comparison-grid article")).toHaveCount(1);
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
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
    path: "../../artifacts/local-qa/mobile-recruitment.png",
    fullPage: true,
  });
});
test("recruitment desktop visual evidence and bounded initial payload", async ({
  page,
}) => {
  const payloads: { url: string; size: number }[] = [];
  page.on("response", async (r) => {
    if (r.url().includes("/data/phase4/")) {
      const b = await r.body();
      payloads.push({ url: r.url(), size: b.length });
    }
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/recruitment/?dataset=wsl");
  await page
    .locator('[data-feature="progressive_passes_per90"] select')
    .first()
    .selectOption("minimum");
  await page
    .locator('[data-feature="progressive_carries_per90"] select')
    .first()
    .selectOption("minimum");
  await page
    .locator('[data-feature="pressures_per90"] select')
    .first()
    .selectOption("minimum");
  await expect(page.locator(".recruitment-table tbody tr")).toHaveCount(10);
  await expect(page.locator(".requirement-name").first()).toContainText(
    "Club role median",
  );
  expect(payloads).toHaveLength(2);
  expect(payloads.reduce((n, p) => n + p.size, 0)).toBeLessThan(270000);
  await page.screenshot({
    path: "../../artifacts/local-qa/desktop-recruitment.png",
    fullPage: true,
  });
});
