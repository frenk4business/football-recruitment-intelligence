# Browser support v1

The supported test matrix is the Chromium, Firefox and WebKit engines supplied by the locked Playwright version, on local macOS and Ubuntu CI. Core product routes and flows run in all three engines. WebKit is a Safari-engine check, not a claim that every macOS/iOS Safari release or physical device was tested. Legacy browsers without Web Crypto/AbortSignal support are outside this release's scope.

The v1 lock uses Playwright 1.63.0: Chromium 153.0.8010.12 (revision 1243), Firefox 155.0 (1543), WebKit 26.6 (2359). Each engine runs 33 scenarios. Eleven scenarios contain 21 axe analyses per engine (63 analyses across the full 99-test suite), including the bilingual route matrix, interactive states and 404 recovery.

The browser suite covers EN/NL navigation, source explorer/tracking slider/search/empty state, Player DNA selection/comparison/thresholds/PCA, translation scenarios/evidence/unavailable states, recruitment custom/replacement/context/hard constraints/comparison/lazy robustness, sharing/locale/reset and strict URL validation. Release checks add actual metadata/headers, 375px/768px/desktop reflow, magnification, keyboard skip/focus, reduced motion, corrupted/stale data retry and 404/no-JavaScript behavior.

WebKit on macOS may require Option-Tab for links, according to the browser/OS keyboard preference; this is tested explicitly. Clipboard writes can be denied by a browser or OS policy. The visible selectable URL fallback remains available; neither a clipboard permission grant nor a backend is required. Horizontal scrolling inside evidence tables/navigation is intentional and keyboard reachable; document-level horizontal overflow is a failure. Static methodology/coverage text and attribution remain useful without JavaScript; interactive tools clearly explain their requirement.

See [release QA](v1-release-qa.md) for exact counts, versions, results and known limits. Review new browser-engine releases through Dependabot rather than changing this support claim without tests.
