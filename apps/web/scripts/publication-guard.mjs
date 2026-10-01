import { createHash } from "node:crypto";
import { posix } from "node:path";
export function validatePublicationPaths(file) {
  for (const [path, prefix] of [
    [file.source, "artifacts/"],
    [file.path, "data/"],
  ]) {
    if (
      !path.startsWith(prefix) ||
      !/^[a-zA-Z0-9_./-]+\.json$/.test(path) ||
      path.includes("..") ||
      posix.normalize(path) !== path
    )
      throw new Error("Unsafe publication path");
  }
}
export function validatePublication(file, data, validate) {
  validatePublicationPaths(file);
  if (data.length > 3_000_000)
    throw new Error(`Oversized artifact: ${file.source}`);
  if (
    data.length !== file.bytes ||
    createHash("sha256").update(data).digest("hex") !== file.sha256
  )
    throw new Error(`Artifact hash mismatch: ${file.source}`);
  const value = JSON.parse(data);
  if (!validate(value)) throw new Error(`Schema failure: ${file.source}`);
}
