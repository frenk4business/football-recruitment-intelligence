/** Presentation identities only. Never used by scientific joins or ranking. */
export function initials(name: string): string {
  const words = name.normalize("NFC").match(/\p{L}[\p{L}\p{M}]*/gu) ?? [];
  if (!words.length) return "?";
  const chosen = words.length === 1 ? [words[0]!] : [words[0]!, words.at(-1)!];
  return chosen.map((w) => Array.from(w)[0].toLocaleUpperCase("en")).join("");
}
export function providerIdentity(id: string): string | null {
  if (/^(statsbomb|wyscout):[0-9]+$/.test(id)) return id;
  const p = /^(statsbomb|wyscout)-[0-9]+-[0-9]+-([0-9]+)$/.exec(id);
  return p ? `${p[1]}:${p[2]}` : null;
}
export type PhotoCredit = {
  path: string;
  author: string;
  license_id: string;
  license_name: string;
  license_url: string;
  commons_page_url: string;
  commons_filename?: string;
  attribution: string;
  credit: string;
  copyright_notice?: string;
  attribution_links: string[];
  transformation: string;
};
export type ImageIndex = {
  version: "player-images-v1";
  identities: Record<string, string>;
  legacy: Record<string, string>;
  assets: Record<string, PhotoCredit>;
};
export function photo(
  index: ImageIndex | null,
  id: string,
): PhotoCredit | null {
  if (!index) return null;
  const key = providerIdentity(id) ?? index.legacy[id];
  return index.assets[index.identities[key]] ?? null;
}
