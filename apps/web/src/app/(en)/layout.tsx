import type { Metadata } from "next";
import { brandIcons } from "@/lib/brand";
import "../globals.css";
export const metadata: Metadata = {
  title: {
    default: "Football Recruitment Intelligence",
    template: "%s · Football Recruitment Intelligence",
  },
  description:
    "Open football data, explicit provenance and reproducible research.",
  icons: brandIcons,
  robots: { index: true, follow: true },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
