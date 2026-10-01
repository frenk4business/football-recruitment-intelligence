"use client";
export function Recovery({
  locale,
  reset,
}: {
  locale: "en" | "nl";
  reset: () => void;
}) {
  const nl = locale === "nl";
  return (
    <main className="recovery" role="alert">
      <h1>
        {nl
          ? "Deze weergave kon niet worden geladen"
          : "This view could not be loaded"}
      </h1>
      <p>
        {nl
          ? "Probeer opnieuw. Vernieuw de pagina als het probleem blijft bestaan; je gedeelde scenario blijft in de URL staan."
          : "Try again. If the problem continues, reload the page; your shared scenario remains in the URL."}
      </p>
      <button onClick={reset}>{nl ? "Opnieuw proberen" : "Try again"}</button>{" "}
      <button onClick={() => window.location.reload()}>
        {nl ? "Pagina vernieuwen" : "Reload page"}
      </button>
      <p>
        <a href={nl ? "/nl/" : "/"}>
          {nl ? "Naar het overzicht" : "Back to overview"}
        </a>
      </p>
    </main>
  );
}
