import { execFileSync } from "node:child_process";
import type { NextConfig } from "next";
const config: NextConfig = {
  output: "export",
  generateBuildId: async () =>
    execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
  productionBrowserSourceMaps: false,
  trailingSlash: true,
  images: { unoptimized: true },
  poweredByHeader: false,
};
export default config;
