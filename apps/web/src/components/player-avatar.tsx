"use client";
import Image from "next/image";
import { useEffect, useState, useSyncExternalStore } from "react";
import type { Locale } from "@/lib/routes";
import { initials, photo, type ImageIndex } from "@/lib/player-images";
import reference from "@/lib/player-image-reference.json";
let index: ImageIndex | null = null;
let pending: Promise<void> | null = null;
const listeners = new Set<() => void>();
const subscribe = (callback: () => void) => {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
};
function load() {
  if (!pending)
    pending = fetch(reference.path, { credentials: "omit" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Image index unavailable");
        const bytes = await response.arrayBuffer();
        if (bytes.byteLength > 650000) throw new Error("Image index too large");
        const hash = Array.from(
          new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
        )
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");
        if (hash !== reference.sha256)
          throw new Error("Image index integrity failed");
        const value = JSON.parse(new TextDecoder().decode(bytes)) as ImageIndex;
        if (value.version !== "player-images-v1")
          throw new Error("Image index version differs");
        index = value;
        listeners.forEach((listener) => listener());
      })
      .catch(() => {
        /* Optional presentation fails closed to initials. Analytics stay usable. */
      });
  return pending;
}
function useImages() {
  const value = useSyncExternalStore(
    subscribe,
    () => index,
    () => null,
  );
  useEffect(() => {
    void load();
  }, []);
  return value;
}
export function PlayerAvatar({
  id,
  name,
  locale,
  size = "small",
  decorative = true,
}: {
  id: string;
  name: string;
  locale: Locale;
  size?: "small" | "medium" | "large";
  decorative?: boolean;
}) {
  const images = useImages();
  const record = photo(images, id);
  const [failed, setFailed] = useState("");
  const dimensions = { small: 32, medium: 64, large: 96 }[size];
  const available = record && record.path !== failed;
  const label =
    locale === "en"
      ? `${name} — ${available ? "player photo" : "No verified player photo available"}`
      : `${name} — ${available ? "spelersfoto" : "Geen geverifieerde spelersfoto beschikbaar"}`;
  return (
    <span
      className={`player-avatar avatar-${size}`}
      aria-hidden={decorative || undefined}
      role={!decorative ? "img" : undefined}
      aria-label={!decorative ? label : undefined}
      style={{ width: dimensions, height: dimensions }}
    >
      {available ? (
        <Image
          src={`/${record.path}`}
          width={dimensions}
          height={dimensions}
          alt=""
          loading="lazy"
          onError={() => setFailed(record.path)}
        />
      ) : (
        <span>{initials(name)}</span>
      )}
    </span>
  );
}
export function PhotoAttribution({
  id,
  name,
  locale,
}: {
  id: string;
  name: string;
  locale: Locale;
}) {
  const images = useImages();
  const record = photo(images, id);
  return (
    <section className="photo-attribution">
      <h4>
        {locale === "en" ? "Photo attribution" : "Fotoverantwoording"} · {name}
      </h4>
      {record ? (
        <>
          <p>
            <a href={record.commons_page_url}>Wikimedia Commons</a> ·{" "}
            {record.author} ·{" "}
            <a href={record.license_url}>{record.license_name}</a>
          </p>
          {record.commons_filename && (
            <p>{record.commons_filename.replace(/^File:/, "")}</p>
          )}
          {record.attribution && <p>{record.attribution}</p>}
          {record.credit && <p>{record.credit}</p>}
          {record.copyright_notice &&
            record.copyright_notice !== record.attribution &&
            record.copyright_notice !== record.credit && (
              <p>{record.copyright_notice}</p>
            )}
          <p>
            {locale === "en"
              ? "Proportionally resized, padded and converted to WebP; no crop. The derived image retains the source licence."
              : "Proportioneel verkleind, opgevuld en naar WebP omgezet; niet uitgesneden. Het afgeleide beeld behoudt de bronlicentie."}
          </p>
          {record.attribution_links.length > 0 && (
            <ul>
              {record.attribution_links.map((url, n) => (
                <li key={url}>
                  <a href={url}>
                    {locale === "en"
                      ? "Original credit link"
                      : "Oorspronkelijke creditlink"}{" "}
                    {n + 1}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </>
      ) : (
        <p>
          {locale === "en"
            ? "No verified player photo available. Initials are presentation only."
            : "Geen geverifieerde spelersfoto beschikbaar. Initialen dienen uitsluitend voor de presentatie."}
        </p>
      )}
    </section>
  );
}
