import { expect, type Page } from "@playwright/test";
export async function expectNoOverflow(page: Page) {
  const report = await page.evaluate(() => ({
    route: location.pathname,
    viewport: innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    offenders:
      document.documentElement.scrollWidth > innerWidth
        ? Array.from(document.querySelectorAll("body *"))
            .filter((e) => {
              if (e.getBoundingClientRect().right <= innerWidth + 1)
                return false;
              for (
                let p = e.parentElement;
                p && p !== document.body;
                p = p.parentElement
              )
                if (
                  ["auto", "hidden", "scroll", "clip"].includes(
                    getComputedStyle(p).overflowX,
                  )
                )
                  return false;
              return true;
            })
            .slice(0, 12)
            .map((e) => ({
              tag: e.tagName,
              class: e.className,
              width: e.getBoundingClientRect().width,
              right: e.getBoundingClientRect().right,
            }))
        : [],
  }));
  expect(report.scrollWidth, JSON.stringify(report)).toBeLessThanOrEqual(
    report.viewport,
  );
}
