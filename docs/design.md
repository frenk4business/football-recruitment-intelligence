# Product and design review

The visual system is warm off-white, charcoal and restrained pitch green, using local system fonts. One navigation row anchors the five sections. Tables carry evidence; no KPI-card grid, gradients, fake badges, recruitment scores or promotional illustrations are used.

The explorer has a single source/match context, one football visual and a paginated roster table. Team and player filters act on the table; the match-level chart says so. Match date, competition/season, sampling scope and source attribution remain visible. Player IDs appear only in secondary source detail, not primary selection labels.

Pitch geometry uses a 105:68 view box and real penalty-area dimensions. Event locations are coarse bins, not a reproduction of the source feed. Tracking markers distinguish detected/extrapolated positions by shape and home/away by letters as well as colour. Each visual has a caption, units, sample context, tooltips and a table alternative. The official StatsBomb logo is attribution rather than project branding.

English and Dutch content is manually typed. Both roots emit the proper HTML language. Keyboard focus, a skip link, semantic tables, labelled native controls, horizontal table scrolling and reduced-motion support are present. Narrow layouts keep readable controls and a compact summary, with no document-level overflow at the tested 390 px width. Automated axe scans target WCAG 2.2 AA checks on all ten pages; this is not a claim of full manual WCAG certification.

Screenshots from an actual Chromium run were reviewed at desktop and mobile widths. The review checked spacing, headings, provider context, no invented evidence and the absence of decorative dashboard clutter. The data loading, failure/retry and no-filter-results states are tested. Missing metrics are textual, distinct from zero; unreliable minutes are explained in a nearby note.
