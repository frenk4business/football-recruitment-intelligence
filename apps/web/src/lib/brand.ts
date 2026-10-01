import type { Metadata } from "next";

export const brandName = "Football Recruitment Intelligence";

// Both language roots use the same explicit icons; public assets work with static export.
export const brandIcons: Metadata["icons"] = {
  icon: [
    { url: "/favicon.ico", type: "image/x-icon", sizes: "16x16 32x32 48x48" },
    { url: "/brand/favicon-32.png", type: "image/png", sizes: "32x32" },
    { url: "/brand/favicon-192.png", type: "image/png", sizes: "192x192" },
  ],
  apple: {
    url: "/brand/apple-touch-icon.png",
    type: "image/png",
    sizes: "180x180",
  },
};
