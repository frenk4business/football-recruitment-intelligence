import { expect, type Page } from "@playwright/test";
export async function expectNoOverflow(page: Page) {
  const removals = await page.evaluate(() => {
    if (document.documentElement.scrollWidth <= innerWidth) return [];
    const result = [];
    for (const e of document.querySelectorAll<HTMLElement>(
      "main section,main div,main select,main svg,main details,main table,main input,main h2,main h3",
    )) {
      const old = e.style.getPropertyValue("display"),
        priority = e.style.getPropertyPriority("display");
      e.style.setProperty("display", "none", "important");
      const width = document.documentElement.scrollWidth;
      if (old) e.style.setProperty("display", old, priority);
      else e.style.removeProperty("display");
      if (width <= innerWidth)
        result.push({
          tag: e.tagName,
          class: e.className,
          label: e.getAttribute("aria-label"),
          text: e.textContent?.slice(0, 80),
        });
    }
    return result.slice(-15);
  });
  const report = await page.evaluate(() => ({
    route: location.pathname,
    viewport: innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    textOverflow:
      document.documentElement.scrollWidth > innerWidth
        ? Array.from(
            document.querySelectorAll(
              "main h2,main h3,main p,main code,main span",
            ),
          )
            .filter((e) => {
              const r = document.createRange();
              r.selectNodeContents(e);
              return (
                r.getBoundingClientRect().right > innerWidth + 1 &&
                e.getBoundingClientRect().right <= innerWidth + 1
              );
            })
            .slice(0, 10)
            .map((e) => ({
              tag: e.tagName,
              class: e.className,
              text: e.textContent?.slice(0, 100),
            }))
        : [],
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
  expect(
    report.scrollWidth,
    JSON.stringify({ ...report, removals }),
  ).toBeLessThanOrEqual(report.viewport);
}
