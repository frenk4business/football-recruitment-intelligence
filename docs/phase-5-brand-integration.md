# Phase 5 — Brand integration

This follow-up integrates the supplied project branding on the current `main` branch after v1.0.0. It does not change the published v1.0.0 tag, research content, frozen artifacts, scientific versions, modelling logic or unrelated interface components.

## Source assets

Inspected all five filenames, PNG signatures, dimensions, colour modes and previews before implementation. Byte-for-byte originals are retained in [`apps/web/brand/source`](../apps/web/brand/source/), outside the public export.

| Supplied filename | Format and dimensions | Use |
| --- | --- | --- |
| `Football Recruitment Intelligence Logo(1).png` | RGB PNG, 1942 × 809 | Horizontal header lockup |
| `Football Recruitment Intelligence.png` | RGB PNG, 1944 × 809 | Reversed white lockup on its supplied dark background; Open Graph sharing image |
| `Soccer Network Ball Emblem.png` | RGBA PNG, 1254 × 1254 | Compact header mark matching the horizontal/white logo family |
| `Network Soccer Ball Icon.png` | RGBA PNG, 1254 × 1254 | Browser favicon and Apple touch icon source |
| `Football Recruitment Intelligence Logo.png` | RGB PNG, 1448 × 1086 | Retained alternate lockup; the matching wider lockup above is used in the header |

No supplied file is literally named “favicon”; the user confirmed the separately supplied `Network Soccer Ball Icon.png` as the favicon source. The site header retains its existing light background. The supplied reversed logo is used on its original dark canvas for sharing, without adding a dark section to the interface.

## Web treatment

Run `npm --prefix apps/web run brand:generate` to reproduce the committed web exports. The offline authoring script uses Sharp already pinned by Next.js in the npm lockfile. Normal builds serve the committed exports and do not require the source files to be public.

The horizontal and compact exports only trim excess outer canvas with clear space retained, resize proportionally, and encode as lossless WebP. The horizontal image is 392 × 126 for a 196 × 63 CSS-pixel display; the compact image is 132 × 132 for a 44 × 44 display at viewport widths up to 480 CSS pixels. Colours, lettering, internal geometry, backgrounds and alpha are preserved; no masking, recolouring, tracing or AI regeneration is applied. The full reversed canvas is resized proportionally to 1200 × 499 and encoded as PNG.

The favicon source receives the same outer-canvas treatment, with transparent 16/32/48-pixel PNG frames in `/favicon.ico`, separate 32- and 192-pixel PNG icons, and a 180-pixel Apple touch PNG. Both Next.js language roots import one metadata definition. The static bilingual 404 also points to the new icons. The previous placeholder SVG is removed.

The header uses a single `<picture>` image with the accessible name “Football Recruitment Intelligence”; its link returns to the current language's homepage. Responsive source selection introduces no duplicate accessible image or extra tab stop. Intrinsic dimensions and CSS reserve space. The existing language switch, navigation, research attribution and provider logo retain their roles.

Only the named web derivatives are added to the public-asset allowlist. The `/brand/*` cache policy already covers the new logos and PNG icons; the favicon cache rule changes from `/favicon.svg` to `/favicon.ico` in both the local header configuration and `render.yaml`. Before a future deployment, apply that path change to the independently managed Render service and verify its actual response. This task makes a local commit; it does not publish or redeploy the site.

## Verification

- `make test`: Python/JavaScript lint, Ruff format, mypy and TypeScript checks, 114 Python tests, 21 JavaScript tests, and generated-contract validation passed. The existing Starlette/httpx deprecation warning remains; there are no test failures.
- `npm --prefix apps/web run check:format`: passed.
- `make release-build`: passed; 16 routes and 2,041 public data artifacts, 43,971,446 exported bytes (below the 50 MB limit). All 2,146 frozen research files passed their existing hash checks.
- Render CLI Blueprint validation: `valid: true`; validation only, no service changes applied.
- Full existing Playwright suite plus brand coverage: 105 checks passed across Chromium, Firefox and WebKit. The new English and Dutch checks cover 320, 375, 480, 481, 768 and 1280 CSS-pixel widths, the compact/lockup switch, undistorted and restrained sizing, separation from the language link, one accessible brand image/link, keyboard focus, locale switching, favicon/Apple metadata, image bytes/dimensions/MIME/cache headers, social metadata and the static 404 favicon. Existing accessibility, reduced-motion, zoom, research interactions and failure/retry checks also passed.
- Visually reviewed the EN/NL overview screenshots at 375 × 900 and 1280 × 900, and the web logo/icon exports. The header remains restrained; there is no logo clipping, stretching, duplicate mark or document overflow. Local screenshots are in the ignored `artifacts/local-qa/brand-{en,nl}-{375,1280}.png` files.
