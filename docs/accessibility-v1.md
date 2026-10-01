# Accessibility review v1

Scope: 16 EN/NL routes, desktop, 768px and 375px layouts, 200% CSS magnification/reflow, normal/reduced-motion preferences, successful and failed-data states. Review combines inspection of rendered screenshots and DOM/ARIA structure, source review and real browser keyboard-event automation. No VoiceOver/NVDA session, physical assistive device or independent human audit is claimed; this is not WCAG certification.

Reviewed against WCAG 2.2 AA criteria within the tested scope.

## Findings and fixes

- A long Dutch homepage heading exceeded narrow columns. Grid children now shrink and headings can wrap/hyphenate under their page language.
- A visually hidden homepage table label escaped its scrolling container. The container now establishes its positioning context; the page stays within the viewport while the evidence table can scroll.
- The new footer version/source links initially overlapped the minimum touch-target space. They now have separated 28px minimum target boxes.
- Recruitment's asynchronous initial data caused baseline CLS 0.2254. Reserved workspace height removes that measured layout shift.
- Linux WebKit's native player selector allowed internal option text to expand document scrolling even while its element fit. Bounded select text and a CSS chevron preserve the native labeled control, option text and keyboard selection without document overflow.
- Recruitment requirement columns respond to container width, including magnification; labels and constraints remain associated with their inputs. Closed disclosures explicitly remove hidden children from layout, wide tables establish a scroll/paint boundary, and long technical/Dutch labels wrap without discarding text. Final Linux verification is recorded in the release QA evidence.

## Reviewed criteria

Skip navigation is the first link and Enter transfers focus to the main landmark. Header navigation has a name and current-page indication; each page has one h1, section headings follow a usable hierarchy, and html lang matches EN/NL. Focus outlines are explicit and survive keyboard operation; focused controls remain reachable in scrolling content. Safari/WebKit on macOS uses Option-Tab to include links under its default keyboard preference; ordinary Tab works for form controls. Tests account for that platform behavior.

Native labeled selects, numeric inputs, checkboxes, range controls, buttons and details/summary retain keyboard behavior. The tracking slider is tested with ArrowRight; candidate selection/comparison and requirement controls are tested with Enter/Space. Copy-link permission denial leaves a labeled, focusable, selectable URL. No pointer-only action is necessary for a core recruitment scenario.

Tables retain captions/headers and textual metric values; charts have nearby numeric/text alternatives and evidence/limitations. Color is not the sole indicator of unavailable values, selection or scores. Axe checks include WCAG 2 A/AA and 2.1/2.2 AA tags in the existing route/flow suite; the requirement is zero violations in those tested contexts, not an assertion about every possible expanded combination. Screen-reader semantics were inspected via accessible snapshots (headings, combobox names, status/alert structure), without pretending those snapshots replace actual assistive-technology testing.

Loading content uses status semantics; data failures use alerts and a retry action; unsupported contexts and no-result states explain their cause. The error boundary offers retry/reload/overview, retaining URL scenario state. Reduced-motion CSS suppresses animations, transitions and smooth scrolling. No automatic pitch animation was introduced. Without JavaScript, methodology/coverage/attribution and navigation remain present and a localized notice explains which tools need JS.

Print CSS removes interactive chrome while keeping research text/tables/attribution. Browser print/export is a convenience, not a certified paginated scientific report; use versioned research documents for formal citation. Native horizontal table scrolling remains intentional. Results, browser versions and unresolved scope limits are in [release QA](v1-release-qa.md).
