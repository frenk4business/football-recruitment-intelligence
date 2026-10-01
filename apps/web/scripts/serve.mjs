import { gzipSync } from "node:zlib";
// Local static export server reproduces release headers and true 404 behavior.
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { resolve, extname } from "node:path";
import { json } from "./release-common.mjs";
const root = resolve("out");
const types = {
  ".html": "text/html; charset=utf-8",
  ".json": "application/json",
  ".js": "text/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml",
};
createServer(async (request, response) => {
  try {
    const path = decodeURIComponent(
      new URL(request.url, "http://localhost").pathname,
    );
    const target = resolve(
      root,
      "." + path,
      path.endsWith("/") ? "index.html" : "",
    );
    if (!target.startsWith(root + "/")) {
      response.writeHead(400);
      response.end();
      return;
    }
    let file = target;
    let status = 200;
    try {
      if (!(await stat(file)).isFile()) throw new Error("Not a file");
    } catch {
      file = resolve(root, "404.html");
      status = 404;
      // Match Render's bounded fallback policy for unknown request paths.
      response.setHeader("Cache-Control", "public, max-age=0, s-maxage=300");
    }
    for (const h of json("config/http-headers.json")) {
      const pattern =
        "^" +
        h.path.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replaceAll("*", ".*") +
        "$";
      if (new RegExp(pattern).test(path)) response.setHeader(h.name, h.value);
    }
    response.setHeader(
      "Content-Type",
      types[extname(file)] ?? "application/octet-stream",
    );
    const body = await readFile(file);
    if (request.headers["accept-encoding"]?.includes("gzip")) {
      response.setHeader("Content-Encoding", "gzip");
      response.setHeader("Vary", "Accept-Encoding");
      response.writeHead(status);
      response.end(gzipSync(body));
    } else {
      response.writeHead(status);
      response.end(body);
    }
  } catch {
    response.writeHead(400);
    response.end();
  }
}).listen(4173, "127.0.0.1", () =>
  console.log("Static release: http://127.0.0.1:4173"),
);
