# Static caching and release consistency

Render applies the rules in `config/http-headers.json`; `render.yaml` contains the equivalent service configuration. Independently created services do not adopt YAML changes automatically. Confirm the actual response after applying settings.

| Resource | Cache-Control | Reason |
| --- | --- | --- |
| HTML, stable JSON, metadata, release manifest, favicon/logo/license | public, max-age=0, must-revalidate | Stable names must validate after release changes |
| /_next/static/* | public, max-age=31536000, immutable | Framework content/build-addressed files |
| /integrity/* | public, max-age=31536000, immutable | SHA-256 filename identifies exact bytes |

More specific rules override the global rule; this precedence was verified on the actual service. Stable `/data` is never marked immutable. Runtime data requests also use `?v=<expected sha256>` and `cache: no-cache`; content verification fails closed even if an old intermediary returns stale data. A small verified hash manifest is cached in memory per directory; rejected manifest requests are evicted so Retry can recover. Selection cancellation does not poison shared manifest loading. Requests have 15-second deadlines and size bounds.

Do not change an immutable asset in place. A changed release gets new framework/integrity filenames. Render deployment cache invalidation plus HTML revalidation normally updates tabs on navigation; already-open tabs that refer to removed old assets must reload. A rollback returns code and its matching artifacts together. No service worker/offline application cache exists. Gzip is verified over the live CDN; Brotli availability depends on negotiation/edge and is not assumed.

All cache policies include `no-transform`: live verification found Cloudflare Polish recompressing the attribution PNG (120,793 → 62,880 bytes). Preserving original exported bytes keeps the complete build hash inventory verifiable; this is distinct from reversible HTTP gzip/Brotli transfer encoding.
