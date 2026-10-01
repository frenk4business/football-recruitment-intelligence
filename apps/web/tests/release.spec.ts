import { expectNoOverflow } from "./layout-check";
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
const version = readFileSync(
  new URL("../../../VERSION", import.meta.url),
  "utf8",
).trim();

for (const locale of ["en", "nl"]) {
  const base = locale === "en" ? "" : "/nl";
  test(`${locale}: responsive brand, favicon and sharing artwork`, async ({
    page,
    request,
  }) => {
    await page.goto(`${base}/`);
    const header = page.locator(".site-header");
    const home = header.getByRole("link", {
      name: "Football Recruitment Intelligence",
      exact: true,
    });
    await expect(home).toHaveCount(1);
    await expect(home).toHaveAttribute("href", `${base}/`);
    await expect(header.getByRole("img")).toHaveCount(1);
    const mark = home.getByRole("img");
    for (const width of [320, 375, 480, 481, 760, 761, 768, 1280]) {
      await page.setViewportSize({ width, height: 812 });
      await expect(mark).toBeVisible();
      await expect
        .poll(() =>
          mark.evaluate((e: HTMLImageElement) =>
            e.complete && e.naturalWidth > 0
              ? new URL(e.currentSrc).pathname
              : "",
          ),
        )
        .toBe(
          width <= 760 ? "/brand/fri-emblem.webp" : "/brand/fri-sidebar.webp",
        );
      const box = (await mark.boundingBox())!;
      expect(box.width).toBeLessThanOrEqual(200);
      expect(box.height).toBeGreaterThanOrEqual(40);
      expect(box.height).toBeLessThanOrEqual(width <= 760 ? 44 : 75);
      const aspect = await mark.evaluate(
        (e: HTMLImageElement) => e.naturalWidth / e.naturalHeight,
      );
      expect(box.width / box.height).toBeCloseTo(aspect, 2);
      const language = (await header.locator(".language").boundingBox())!;
      expect(box.x + box.width + 24).toBeLessThanOrEqual(language.x);
      await expectNoOverflow(page);
    }
    await home.focus();
    await expect(home).toBeFocused();
    await header.locator(".language").click();
    await expect(page.locator("html")).toHaveAttribute(
      "lang",
      locale === "en" ? "nl" : "en",
    );
    await page.goto(`${base}/`);
    for (const [rel, path, type, sizes] of [
      ["icon", "/favicon.ico", "image/x-icon", "16x16 32x32 48x48"],
      ["icon", "/brand/favicon-32.png", "image/png", "32x32"],
      ["icon", "/brand/favicon-192.png", "image/png", "192x192"],
      [
        "apple-touch-icon",
        "/brand/apple-touch-icon.png",
        "image/png",
        "180x180",
      ],
    ]) {
      const link = page.locator(`link[rel="${rel}"][href="${path}"]`);
      await expect(link).toHaveCount(1);
      await expect(link).toHaveAttribute("sizes", sizes);
      await expect(link).toHaveAttribute("type", type);
      const asset = await request.get(path);
      expect(asset.status()).toBe(200);
      expect(asset.headers()["content-type"]).toMatch(
        type === "image/png"
          ? /^image\/png/
          : /^image\/(?:x-icon|vnd\.microsoft\.icon)/,
      );
      expect(asset.headers()["cache-control"]).toContain("must-revalidate");
      if (type === "image/png") {
        const png = await asset.body();
        const [w, h] = sizes.split("x").map(Number);
        expect(png.readUInt32BE(16)).toBe(w);
        expect(png.readUInt32BE(20)).toBe(h);
      } else {
        const ico = await asset.body();
        expect(ico.readUInt16LE(2)).toBe(1);
        expect(ico.readUInt16LE(4)).toBe(3);
      }
    }
    await expect(page.locator('link[href="/favicon.svg"]')).toHaveCount(0);
    await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
      "content",
      "https://football-recruitment-intelligence.onrender.com/brand/fri-social.png",
    );
    await expect(page.locator('meta[property="og:image:alt"]')).toHaveAttribute(
      "content",
      "Football Recruitment Intelligence",
    );
    const social = await request.get("/brand/fri-social.png");
    expect(social.status()).toBe(200);
    expect(social.headers()["content-type"]).toContain("image/png");
  });
  test(`${locale}: release metadata, keyboard, responsive layout and reduced motion`, async ({
    page,
    browserName,
  }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    for (const width of [375, 768, 1280]) {
      await page.setViewportSize({ width, height: 812 });
      for (const route of [
        "",
        "player-dna/",
        "translation/",
        "recruitment/",
        "methodology/",
      ]) {
        await page.goto(`${base}/${route}`);
        if (route === "player-dna/")
          await expect(page.locator(".dna-header h2")).toBeVisible();
        if (route === "translation/")
          await expect(page.locator(".translation-player")).toBeVisible();
        if (route === "recruitment/")
          await expect(page.locator(".recruitment-empty")).toBeVisible();
        await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
          "href",
          `https://football-recruitment-intelligence.onrender.com${base}/${route}`,
        );
        await expect(page.locator('link[hreflang="en"]')).toHaveCount(1);
        await expect(page.locator('link[hreflang="nl"]')).toHaveCount(1);
        await expect(page.locator('meta[name="robots"]')).not.toHaveAttribute(
          "content",
          /noindex/,
        );
        await expectNoOverflow(page);
      }
    }
    await page.goto(`${base}/recruitment/`);
    await expect(page.locator(".recruitment-empty")).toBeVisible();
    await page.keyboard.press(browserName === "webkit" ? "Alt+Tab" : "Tab");
    await expect(page.locator(".skip-link")).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.locator("#main")).toBeFocused();
    await expect(
      page.getByRole("link", { name: `v${version}`, exact: true }),
    ).toBeVisible();
    expect(
      await page
        .locator("main")
        .evaluate((e) => getComputedStyle(e).animationName),
    ).toBe("none");
    await page.locator("body").evaluate((e) => {
      e.style.zoom = "2";
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const tree = await page.locator("main").ariaSnapshot();
    expect(tree).toContain("heading");
    expect(tree).toContain("combobox");
  });
  for (const [route, pattern, ready] of [
    ["explorer", "**/data/explorer/*.json*", ".explorer-results"],
    ["player-dna", "**/data/phase2/900/*.json*", ".dna-header h2"],
    ["translation", "**/data/phase3/players/*.json*", ".translation-panel"],
    ["recruitment", "**/data/phase4/index.json*", ".recruitment-empty"],
  ]) {
    test(`${locale}: ${route} rejects malformed and stale data, then recovers`, async ({
      page,
    }) => {
      const errors: string[] = [];
      page.on("pageerror", (e) => errors.push(e.message));
      await page.route(pattern, (r) =>
        r.fulfill({
          status: 200,
          contentType: "application/json",
          body: '{"version":"future-v99"}',
        }),
      );
      await page.goto(`${base}/${route}/`);
      await expect(
        page.locator("main").getByRole("alert").first(),
      ).toBeVisible();
      await expect(
        page.getByRole("button", {
          name: locale === "en" ? "Try again" : "Opnieuw proberen",
          exact: true,
        }),
      ).toBeVisible();
      await page.unroute(pattern);
      await page
        .getByRole("button", {
          name: locale === "en" ? "Try again" : "Opnieuw proberen",
          exact: true,
        })
        .click();
      await expect(page.locator("main").getByRole("alert")).toHaveCount(0);
      if (route === "explorer")
        await expect(
          page.getByRole("heading", { name: /Argentina/ }),
        ).toBeVisible();
      else if (route === "translation")
        await expect(page.locator(".translation-player")).toBeVisible();
      else await expect(page.locator(ready)).toBeVisible();
      expect(errors).toEqual([]);
    });
  }
}

test("static 404, robots, sitemap and JavaScript-disabled content", async ({
  page,
  request,
  browser,
}) => {
  const response = await page.goto("/not-a-real-route/");
  expect(response?.status()).toBe(404);
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute(
    "href",
    "/favicon.ico",
  );
  await expect(
    page.getByRole("link", { name: "English overview" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Nederlands overzicht" }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(await (await request.get("/robots.txt")).text()).not.toContain(
    "Disallow: /\n",
  );
  const sitemap = await (await request.get("/sitemap.xml")).text();
  expect(sitemap.match(/<loc>/g)).toHaveLength(20);
  const context = await browser.newContext({ javaScriptEnabled: false });
  const noJS = await context.newPage();
  await noJS.goto(new URL("/methodology/", page.url()).href);
  await expect(noJS.locator("noscript p")).toContainText("requires JavaScript");
  await expect(noJS.locator("main h1")).toBeVisible();
  await expect(
    noJS.getByRole("navigation", { name: "Main navigation" }),
  ).toBeVisible();
  await context.close();
});

test("security headers enforce same-origin resources and stable data revalidation", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const response = await page.goto("/recruitment/");
  const headers = response!.headers();
  expect(headers["content-security-policy"]).toContain(
    "frame-ancestors 'none'",
  );
  expect(headers["content-security-policy"]).not.toContain("unsafe-eval");
  expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  expect(headers["permissions-policy"]).toContain("camera=()");
  expect(headers["x-content-type-options"]).toBe("nosniff");
  await expect(page.locator(".recruitment-empty")).toBeVisible();
  const data = await request.get("/data/phase4/index.json");
  expect(data.headers()["x-robots-tag"]).toBe("noindex");
  expect(data.headers()["cache-control"]).toContain("max-age=0");
  const script = await page
    .locator('script[src*="/_next/static/"]')
    .first()
    .getAttribute("src");
  const asset = await request.get(script!);
  expect(asset.headers()["cache-control"]).toContain("immutable");
  expect(errors).toEqual([]);
});

test("clipboard denial retains a selectable share URL", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => {
          throw new DOMException("Denied", "NotAllowedError");
        },
      },
    });
  });
  await page.goto("/recruitment/");
  await page
    .locator('[data-feature="pressures_per90"] select')
    .first()
    .selectOption("minimum");
  await page
    .getByRole("button", { name: "Copy scenario link", exact: false })
    .click();
  const fallback = page.getByLabel("Copy this scenario link", { exact: true });
  await expect(fallback).toHaveValue(/v=1/);
  await fallback.focus();
  await expect(fallback).toBeFocused();
  await expect(
    page.getByText("Copy the link below to share this scenario.", {
      exact: false,
    }),
  ).toBeVisible();
});
