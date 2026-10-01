import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Locale } from "@/lib/routes";
import type { PhotoCredit } from "@/lib/player-images";
export function ImageCredits({ locale }: { locale: Locale }) {
  const manifest = JSON.parse(
    readFileSync(
      join(process.cwd(), "../../artifacts/player-images/manifest.json"),
      "utf8",
    ),
  ) as {
    assets: Record<string, PhotoCredit>;
    identities: Record<string, { name: string; asset: string }>;
  };
  return (
    <section id="image-credits" className="image-credits">
      <h2>
        {locale === "en" ? "Player image credits" : "Credits spelersfoto’s"}
      </h2>
      <p>
        {locale === "en"
          ? "Player photos are separate presentation metadata from Wikidata and Wikimedia Commons, not football-provider imagery. Copyright reuse is checked; this is not a universal assessment of personality rights. Photos do not enter any model or ranking."
          : "Spelersfoto’s zijn afzonderlijke presentatiegegevens uit Wikidata en Wikimedia Commons, geen beeldmateriaal van de voetbalproviders. Hergebruik onder auteursrecht wordt gecontroleerd; dit is geen universele beoordeling van persoonlijkheidsrechten. Foto’s worden niet gebruikt in modellen of ranglijsten."}
      </p>
      <p>
        {locale === "en"
          ? "Images are proportionally resized, padded and converted to WebP without cropping. Derived images retain their source licence, including share-alike terms where applicable."
          : "Beelden worden proportioneel verkleind, opgevuld en naar WebP omgezet zonder uitsnede. Afgeleide beelden behouden hun bronlicentie, inclusief de gelijkdelenvoorwaarden waar van toepassing."}
      </p>
      <p>
        {locale === "en"
          ? "Photo dates and kits may differ from the selected data season. An available photo does not imply better data coverage or a stronger player."
          : "Fotodatums en tenues kunnen afwijken van het geselecteerde dataseizoen. Een beschikbare foto betekent niet dat de datadekking beter is of de speler sterker is."}
      </p>
      <p>
        <a href={`/players/images/credits-${locale}.html`}>
          {locale === "en"
            ? "All photo sources and licences"
            : "Alle fotobronnen en licenties"}
        </a>{" "}
        ({Object.keys(manifest.assets).length})
      </p>
    </section>
  );
}
