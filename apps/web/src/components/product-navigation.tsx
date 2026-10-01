import Link from "next/link";
import { copy, route, type Locale, type Section } from "@/lib/content";
export function ProductNavigation({
  locale,
  section,
}: {
  locale: Locale;
  section: Section;
}) {
  const current =
    section === "player-dna"
      ? "players"
      : ["home", "players", "recruitment"].includes(section)
        ? section
        : "research";
  const links = (["players", "recruitment", "research"] as const).map((s) => (
    <Link
      prefetch={false}
      key={s}
      href={route(locale, s)}
      aria-current={s === current ? "page" : undefined}
    >
      {copy[locale].nav[s]}
    </Link>
  ));
  const label = locale === "en" ? "Main navigation" : "Hoofdnavigatie";
  return (
    <>
      <nav className="product-nav desktop-navigation" aria-label={label}>
        {links}
      </nav>
      <details className="mobile-menu" key={`${locale}-${section}`}>
        <summary>Menu</summary>
        <nav id="product-navigation" className="product-nav" aria-label={label}>
          {links}
        </nav>
      </details>
    </>
  );
}
