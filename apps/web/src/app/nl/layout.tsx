import type { Metadata } from "next";
import { brandIcons } from "@/lib/brand";
import "../globals.css";
import "@/styles/product.css";
export const metadata: Metadata = {
  title: {
    default: "Football Recruitment Intelligence",
    template: "%s · Football Recruitment Intelligence",
  },
  description:
    "Open voetbaldata, zichtbare herkomst en reproduceerbaar onderzoek.",
  icons: brandIcons,
  robots: { index: true, follow: true },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}
