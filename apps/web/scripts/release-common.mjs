import { readFileSync, readdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
export const root = fileURLToPath(new URL("../../../", import.meta.url));
export const read = (path) =>
  readFileSync(new URL(path, new URL("../../../", import.meta.url)));
export const json = (path) => JSON.parse(read(path));
export const sha = (data) => createHash("sha256").update(data).digest("hex");
export const version = read("VERSION").toString().trim();
export const inventory = {
  files: [
    ...json("config/public-artifacts.json").files,
    ...json("config/v11-public-artifacts.json").files,
  ],
};
export const science = json("config/scientific-lock.json");
export const git = (...args) =>
  execFileSync("git", args, { cwd: root, encoding: "utf8" }).trim();
export const walk = (dir) =>
  readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    if (entry.isSymbolicLink())
      throw new Error(`Symlink rejected: ${dir}/${entry.name}`);
    return entry.isDirectory()
      ? walk(`${dir}/${entry.name}`)
      : [`${dir}/${entry.name}`];
  });
export function verifyScience() {
  for (const [path, digest] of Object.entries(science.files)) {
    if (sha(read(path)) !== digest)
      throw new Error(`Scientific lock mismatch: ${path}`);
  }
}
