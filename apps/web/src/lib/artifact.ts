import groups from "./artifact-integrity.json";

const manifests = new Map<string, Promise<Record<string, string>>>();
async function digest(bytes: ArrayBuffer): Promise<string> {
  return Array.from(
    new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    (b) => b.toString(16).padStart(2, "0"),
  ).join("");
}
async function verifiedJSON(
  url: string,
  expected: string,
  signal: AbortSignal,
  limit: number,
): Promise<unknown> {
  const response = await fetch(url, {
    signal,
    cache: "no-cache",
    credentials: "omit",
    redirect: "error",
  });
  if (
    !response.ok ||
    !response.headers.get("content-type")?.includes("application/json")
  )
    throw new Error("Unavailable data");
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Missing data");
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > limit) {
      await reader.cancel();
      throw new Error("Data size mismatch");
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  if ((await digest(bytes.buffer)) !== expected)
    throw new Error("Data version mismatch; reload this release");
  return JSON.parse(new TextDecoder().decode(bytes));
}
/** Only exact build-validated bytes may become a typed contract. The hash index
 * is pinned in the JS bundle, so stale data/index responses fail closed. */
export async function fetchArtifact<T>(
  path: string,
  signal: AbortSignal,
): Promise<T> {
  const group = groups.find((g) => path.startsWith(g.prefix));
  if (!group || path.includes("..") || path.includes("?"))
    throw new Error("Unknown artifact");
  const boundedSignal = AbortSignal.any([signal, AbortSignal.timeout(15_000)]);
  // Manifest requests have their own bounded lifecycle; a cancelled player request
  // must not poison the shared cache for the next player selection.
  let manifest = manifests.get(group.path);
  if (!manifest) {
    manifest = verifiedJSON(
      group.path,
      group.sha256,
      AbortSignal.timeout(15_000),
      200_000,
    ).then((v) => v as Record<string, string>);
    manifests.set(group.path, manifest);
    manifest.catch(() => manifests.delete(group.path));
  }
  const hashes = await manifest;
  boundedSignal.throwIfAborted();
  if (!Object.hasOwn(hashes, path)) throw new Error("Unknown artifact");
  const value = await verifiedJSON(
    `${path}?v=${hashes[path]}`,
    hashes[path],
    boundedSignal,
    3_000_000,
  );
  boundedSignal.throwIfAborted();
  return value as T;
}
