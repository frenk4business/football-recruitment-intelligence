"use client";
import { useState } from "react";
import Link from "next/link";
import { copy, route, type Locale, type Section } from "@/lib/content";
export function ProductNavigation({
  locale,
  section,
}: {
  locale: Locale;
  section: Section;
}) {
  const [open, setOpen] = useState(false);
  const current =
    section === "player-dna"
      ? "players"
      : ["home", "players", "recruitment"].includes(section)
        ? section
        : "research";
  return (
    <>
      <button
        className="menu-toggle"
        aria-expanded={open}
        aria-controls="product-navigation"
        onClick={() => setOpen(!open)}
      >
        {open ? (locale === "en" ? "Close" : "Sluiten") : "Menu"}
      </button>
      <nav
        id="product-navigation"
        className={open ? "product-nav is-open" : "product-nav"}
        aria-label={locale === "en" ? "Main navigation" : "Hoofdnavigatie"}
      >
        {(["players", "recruitment", "research"] as const).map((s) => (
          <Link
            prefetch={false}
            key={s}
            href={route(locale, s)}
            aria-current={s === current ? "page" : undefined}
            onClick={() => setOpen(false)}
          >
            {copy[locale].nav[s]}
          </Link>
        ))}
      </nav>
    </>
  );
}
