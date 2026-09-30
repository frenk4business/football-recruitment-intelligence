import type { PlayerSummary } from "./contracts.ts";
export function filterPlayers(
  rows: PlayerSummary[],
  team: string,
  query: string,
): PlayerSummary[] {
  const text = query
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
  return rows.filter(
    (p) =>
      (!team || p.team === team) &&
      p.name
        .normalize("NFD")
        .replace(/\p{Diacritic}/gu, "")
        .toLowerCase()
        .includes(text),
  );
}
export function metric(
  value: number | null,
  locale: string,
  unavailable: string,
  digits = 0,
): string {
  return value === null
    ? unavailable
    : new Intl.NumberFormat(locale, { maximumFractionDigits: digits }).format(
        value,
      );
}
