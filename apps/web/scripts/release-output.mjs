import { readFileSync, writeFileSync, existsSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import {
  root,
  json,
  sha,
  version,
  inventory,
  walk,
  git,
  verifyScience,
} from "./release-common.mjs";
const out = join(root, "apps/web/out");
const check = process.argv.includes("--check");
const origin = "https://football-recruitment-intelligence.onrender.com";
const sections = [
  "",
  "explorer",
  "player-dna",
  "translation",
  "recruitment",
  "methodology",
  "coverage",
];
// Read actual route directories too: evaluation/research routes are first-class pages.
const pages = walk(out).filter(
  (p) =>
    p.endsWith("/index.html") &&
    !p.includes("/_next/") &&
    !p.includes("/404/") &&
    !p.includes("/_not-found/"),
);
const routes = pages
  .map((p) => "/" + relative(out, p).replace(/index\.html$/, ""))
  .sort();
if (!check) {
  writeFileSync(
    join(out, "robots.txt"),
    `User-agent: *\nAllow: /\nDisallow: /data/\nDisallow: /integrity/\nDisallow: /release-manifest.json\nSitemap: ${origin}/sitemap.xml\n`,
  );
  writeFileSync(
    join(out, "sitemap.xml"),
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      routes.map((r) => `<url><loc>${origin}${r}</loc></url>`).join("\n") +
      "\n</urlset>\n",
  );
  writeFileSync(
    join(out, "404.html"),
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Page not found · Football Recruitment Intelligence</title><style>body{font:18px/1.6 system-ui;color:#173c35;background:#f4f2ea;max-width:720px;margin:12vh auto;padding:24px}a{color:inherit;text-underline-offset:4px}a:focus-visible{outline:3px solid #236044;outline-offset:5px}nav{display:flex;gap:24px;flex-wrap:wrap}</style></head><body><main><p>Football Recruitment Intelligence</p><h1>Page not found</h1><p>This address does not exist. Return to an overview or the methodology.</p><nav aria-label="Recovery"><a href="/">English overview</a><a href="/methodology/">Methodology</a></nav><section lang="nl"><h2>Pagina niet gevonden</h2><p>Dit adres bestaat niet. Ga terug naar het overzicht of de methodologie.</p><nav aria-label="Herstel"><a href="/nl/">Nederlands overzicht</a><a href="/nl/methodology/">Methodologie</a></nav></section></main></body></html>',
  );
  const manifest = json("apps/web/public/release-manifest.json");
  manifest.build_files = Object.fromEntries(
    walk(out)
      .filter((p) => !p.endsWith("/release-manifest.json"))
      .sort()
      .map((p) => [
        relative(out, p),
        { bytes: statSync(p).size, sha256: sha(readFileSync(p)) },
      ]),
  );
  writeFileSync(
    join(out, "release-manifest.json"),
    JSON.stringify(manifest, null, 2) + "\n",
  );
}
verifyScience();
const manifest = JSON.parse(readFileSync(join(out, "release-manifest.json")));
if (
  manifest.version !== version ||
  manifest.git_commit !== git("rev-parse", "HEAD")
)
  throw new Error("Build belongs to a different commit/version; rebuild");
const actual = walk(out)
  .map((p) => relative(out, p))
  .filter((p) => p !== "release-manifest.json")
  .sort();
if (
  JSON.stringify(actual) !==
  JSON.stringify(Object.keys(manifest.build_files).sort())
)
  throw new Error("Unexpected output file");
for (const [path, metadata] of Object.entries(manifest.build_files)) {
  if (sha(readFileSync(join(out, path))) !== metadata.sha256)
    throw new Error(`Build checksum mismatch: ${path}`);
  if (
    /\.(map|parquet|duckdb|nc|pyc)$|(^|\/)\.env|posterior|(^|\/)raw\//.test(
      path,
    )
  )
    throw new Error(`Forbidden output: ${path}`);
}
const actualData = actual.filter((p) => p.startsWith("data/"));
if (
  JSON.stringify(actualData) !==
  JSON.stringify(inventory.files.map((f) => f.path).sort())
)
  throw new Error("Public allowlist mismatch");
for (const f of inventory.files)
  if (sha(readFileSync(join(out, f.path))) !== f.sha256)
    throw new Error(`Public checksum mismatch: ${f.path}`);
let total = walk(out).reduce((n, p) => n + statSync(p).size, 0);
if (total > 50_000_000)
  throw new Error(`Export size budget exceeded: ${total}`);
for (const locale of ["", "nl/"])
  for (const section of sections)
    if (!routes.includes(`/${locale}${section}${section ? "/" : ""}`))
      throw new Error(`Missing route: ${locale}${section}`);
let references = 0;
for (const path of pages) {
  const html = readFileSync(path, "utf8");
  if (html.includes('name="robots" content="noindex'))
    throw new Error(`Production page noindex: ${path}`);
  if (
    !html.includes('rel="canonical"') ||
    (!html.includes('hrefLang="nl"') && !html.includes('hreflang="nl"'))
  )
    throw new Error(`Missing canonical/languages: ${path}`);
  for (const match of html.matchAll(
    /(?:href|src)="(\/[^"?#]*)(?:[?#][^"]*)?"/g,
  )) {
    const target = decodeURIComponent(match[1]);
    if (
      !existsSync(join(out, target, target.endsWith("/") ? "index.html" : ""))
    )
      throw new Error(
        `Broken internal reference: ${target} in ${relative(out, path)}`,
      );
    references++;
  }
}
console.log(
  `Release ${version}: ${routes.length} routes, ${inventory.files.length} public artifacts, ${references} internal references, ${total} export bytes validated.`,
);
