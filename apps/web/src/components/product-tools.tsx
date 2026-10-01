"use client";
import dynamic from "next/dynamic";
// Load interactive workspaces only on routes that use them. Server rendering stays
// enabled so research conclusions remain readable without JavaScript.
export const Players = dynamic(() =>
  import("./players").then((m) => m.Players),
);
export const Recruitment = dynamic(() =>
  import("./recruitment").then((m) => m.Recruitment),
);
export const PlayerDNA = dynamic(() =>
  import("./player-dna").then((m) => m.PlayerDNA),
);
export const Evaluation = dynamic(() =>
  import("./player-dna").then((m) => m.Evaluation),
);
export const Translation = dynamic(() =>
  import("./translation").then((m) => m.Translation),
);
export const TranslationEvaluation = dynamic(() =>
  import("./translation").then((m) => m.TranslationEvaluation),
);
export const Explorer = dynamic(() =>
  import("./explorer").then((m) => m.Explorer),
);
