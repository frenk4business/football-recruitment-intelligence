import type { Metadata } from "next";
import "../globals.css";
export const metadata: Metadata = {
  title: {
    default: "Football Recruitment Intelligence",
    template: "%s · Football Recruitment Intelligence",
  },
  description:
    "Open voetbaldata, zichtbare herkomst en reproduceerbaar onderzoek.",
  robots: { index: false, follow: true },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}
