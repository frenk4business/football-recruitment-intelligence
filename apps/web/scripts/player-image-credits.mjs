// Plain static credits avoid serializing hundreds of entries into every RSC payload.
const escape = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const paragraph = (v) => (v ? "<p>" + escape(v) + "</p>" : "");
const link = (url, label) =>
  '<a href="' + escape(url) + '">' + escape(label) + "</a>";
export function creditsHtml(manifest, locale) {
  const en = locale === "en";
  const title = en ? "Player image credits" : "Credits spelersfoto’s";
  const research = en
    ? "/research/#image-credits"
    : "/nl/research/#image-credits";
  const entries = Object.entries(manifest.assets)
    .map(([hash, a]) => {
      const names = [
        ...new Set(
          Object.values(manifest.identities)
            .filter((p) => p.asset === hash)
            .map((p) => p.name),
        ),
      ];
      return (
        '<li id="photo-' +
        hash +
        '"><h2>' +
        escape(names.join(" / ")) +
        "</h2>" +
        paragraph(a.commons_filename.replace(/^File:/, "")) +
        "<p>" +
        link(a.commons_page_url, "Wikimedia Commons") +
        " · " +
        escape(a.author) +
        " · " +
        link(a.license_url, a.license_name) +
        " · " +
        link("/" + a.path, en ? "Derived image" : "Afgeleid beeld") +
        "</p>" +
        paragraph(a.attribution) +
        paragraph(a.credit) +
        paragraph(
          a.copyright_notice !== a.attribution &&
            a.copyright_notice !== a.credit
            ? a.copyright_notice
            : "",
        ) +
        (a.attribution_links.length
          ? "<ul>" +
            a.attribution_links
              .map(
                (url, n) =>
                  "<li>" +
                  link(
                    url,
                    (en
                      ? "Original credit link "
                      : "Oorspronkelijke creditlink ") +
                      (n + 1),
                  ) +
                  "</li>",
              )
              .join("") +
            "</ul>"
          : "") +
        "</li>"
      );
    })
    .join("");
  const note = en
    ? "Images are proportionally resized, padded and converted to WebP without cropping. Each derived image retains its source licence, including share-alike terms where applicable. Photos do not enter models or rankings. Photo dates and kits may differ from the data season. Copyright checks do not establish universal personality-right clearance."
    : "Beelden worden proportioneel verkleind, opgevuld en naar WebP omgezet zonder uitsnede. Elk afgeleid beeld behoudt de bronlicentie, inclusief gelijkdelenvoorwaarden waar van toepassing. Foto’s worden niet gebruikt in modellen of ranglijsten. Fotodatums en tenues kunnen afwijken van het dataseizoen. Auteursrechtcontroles bieden geen universele vrijwaring van persoonlijkheidsrechten.";
  return (
    '<!doctype html><html lang="' +
    locale +
    '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' +
    title +
    ' · Football Recruitment Intelligence</title><link rel="icon" href="/favicon.ico"><link rel="canonical" href="https://football-recruitment-intelligence.onrender.com/players/images/credits-' +
    locale +
    '.html">' +
    "<style>body{margin:0;background:#f5f7f8;color:#20313e;font:16px/1.6 system-ui}header,main{max-width:960px;margin:auto;padding:24px}header{display:flex;gap:24px;flex-wrap:wrap;align-items:center;justify-content:space-between;background:white}a{color:#236044;text-underline-offset:3px;overflow-wrap:anywhere}a:focus-visible{outline:3px solid #236044;outline-offset:4px}.brand{display:flex;gap:12px;align-items:center;font-weight:600;color:#20313e;text-decoration:none}nav{display:flex;gap:24px}h1{font-size:28px}h2{font-size:19px}p{overflow-wrap:anywhere}.credits{list-style:none;padding:0}.credits>li{padding:20px 0;border-top:1px solid #ced7de}p{margin:8px 0}</style></head><body><header>" +
    '<a class="brand" href="' +
    (en ? "/" : "/nl/") +
    '"><img src="/brand/fri-emblem.webp" alt="" width="32" height="32">Football Recruitment Intelligence</a><nav aria-label="' +
    (en ? "Navigation" : "Navigatie") +
    '">' +
    link(research, en ? "Back to Research" : "Terug naar Research") +
    link("credits-" + (en ? "nl" : "en") + ".html", en ? "NL" : "EN") +
    "</nav></header><main><h1>" +
    title +
    "</h1>" +
    paragraph(note) +
    paragraph(
      Object.keys(manifest.assets).length +
        (en
          ? " approved images. Football-data and image licences are separate."
          : " goedgekeurde beelden. Voetbaldata en beelden hebben afzonderlijke licenties."),
    ) +
    '<ul class="credits">' +
    entries +
    "</ul></main></body></html>\n"
  );
}
