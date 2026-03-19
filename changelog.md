# Changelog: Research pages merge

## Summary

Merged `/research-program.html` and `/tokenomics-research.html` into a single canonical research page at `/selected-research.html`. The two retired URLs now redirect so existing links do not break. No paper or output was removed.

## Files changed

| File | Change |
|------|--------|
| `selected-research.html` | Rewritten as canonical research library: program overview, best-first-read, filters/jump links, Track A, Track B, earlier work, cross-track convergence. Title set to "Research \| Zach Zukowski". Meta description and OG updated. |
| `research-program.html` | Replaced with lightweight redirect: canonical to selected-research.html, JS redirect to `/selected-research.html#program-overview`, noscript fallback. |
| `tokenomics-research.html` | Replaced with lightweight redirect: canonical to selected-research.html, JS redirect to `/selected-research.html#track-b`, noscript fallback. |
| `index.html` | Three links updated: Research program send-item and research footer link → `selected-research.html#program-overview`; Tokenomics & DePIN track → `selected-research.html#track-b`. |
| `start-here.html` | Two links updated: Tokenomics & DePIN track → `selected-research.html#track-b`; View the full research program → `selected-research.html#program-overview`. |
| `frameworks.html` | Two links updated: View the full research program → `selected-research.html#program-overview` (parenthetical "eight papers, two tracks" removed); Tokenomics & DePIN track → `selected-research.html#track-b`. |
| `resume/stablecoin-payments-strategy.html` | Tokenomics & DePIN track link → `selected-research.html#track-b`. |
| `resume/asset-management-tokenization.html` | Tokenomics & DePIN track link → `selected-research.html#track-b`. |
| `resume/policy-market-infrastructure.html` | Tokenomics & DePIN track link → `selected-research.html#track-b`. |
| `papers/adaptive-tokenomics.html` | All three references to tokenomics-research.html → `selected-research.html#track-b`. |
| `papers/operational-risk-token-economies.html` | All three references to tokenomics-research.html → `selected-research.html#track-b`. |

## Final section structure (selected-research.html)

1. **#program-overview** – Program overview: two-track thesis (Track A = stablecoin/dollar infrastructure, Track B = tokenomics/DePIN), convergence line, and one-line library framing ("Core program papers, public articles, and earlier work, all on one page.").
2. **#best-first-read** – Featured paper: Routing the Dollar (Under review, Best first read), with metadata, thesis, blurb, CTAs (paper summary, SSRN, Thread), cover image, and "More on relevance and audience" expandable.
3. **Filters and jump links** – Audience, Track, Status filters (unchanged). Jump links: #best-first-read, #track-a, #track-b, #earlier-work, #cross-track-convergence.
4. **#track-a** – Track A: short intro, A1 compact reference only ("A1 — Routing the Dollar — featured above."), then full cards for A2 (Minimum Viable Equivalence Packs), Dollar v3 / The Control Layer War (no A3 label), Tokenized Equity, Navigating the New Era of Digital Assets.
5. **#track-b** – Track B: short intro, then full cards for B1 (Adaptive Tokenomics, Public + Code available), B2 (Tokenomics as Institutional Design, Available on request), B3 (GeoDePIN, Available on request), B4 (Operational Risk in Token Economies, Public + Code available); then muted thesis note (Draft BSc thesis wrapping B2 and B3).
6. **#earlier-work** – Three cards: The Future of Tokenomics (Medium, Aug 2024), Gamification in Crypto (Medium, Aug 2024), Introduction to Tokenomics (Medium, Apr 2022).
7. **#cross-track-convergence** – Tightened three-row table (Dimension: Infrastructure concentration, Stress transmission, Subsidy-to-revenue transition) with one-sentence cells per track, plus synthesis line: "Both tracks find that infrastructure-layer analysis reveals failure modes invisible to asset-level monitoring."

## Papers and outputs included (no loss)

| Item | Location | Badges / notes |
|------|----------|----------------|
| Routing the Dollar | Featured (#best-first-read) + A1 ref in Track A | Under review, Best first read |
| Minimum Viable Equivalence Packs (A2) | Track A | Public |
| Dollar v3 / The Control Layer War | Track A | Public / requestable |
| Tokenized Equity | Track A | Public, Medium |
| Navigating the New Era of Digital Assets | Track A | Public, Medium |
| Adaptive Tokenomics (B1) | Track B | Public, Code available |
| Tokenomics as Institutional Design (B2) | Track B | Available on request |
| GeoDePIN (B3) | Track B | Available on request |
| Operational Risk in Token Economies (B4) | Track B | Public, Code available |
| BSc thesis (B2 + B3 umbrella) | Track B (muted note) | Draft |
| The Future of Tokenomics | Earlier work | Public, Medium Aug 2024 |
| Gamification in Crypto | Earlier work | Public, Medium Aug 2024 |
| Introduction to Tokenomics | Earlier work | Public, Medium Apr 2022 |

## SEO / metadata

- **selected-research.html**: `<title>Research | Zach Zukowski</title>`. Meta description: "Two research tracks, one thesis: regulate the operator, not just the token. Papers on stablecoin infrastructure, dollar tokenization, DePIN mechanism design, and operational risk." Canonical and OG point to `https://www.cryptozach.com/selected-research.html`.
- **research-program.html** and **tokenomics-research.html**: Canonical points to `https://www.cryptozach.com/selected-research.html`; no duplicate content.

## What was not changed

- Individual paper summary URLs (e.g. `/papers/routing-the-dollar.html`) unchanged.
- Main nav "Research" still points to `selected-research.html`.
- Homepage "8 papers" stat badge unchanged.
- Card and expand/collapse pattern ("More on relevance and audience", "Why it matters", "Who it's for") preserved.
- Existing badge vocabulary only (no "Submitted", "Published", "Final draft" added).

## Unresolved questions

- None. All internal links were updated; "eight papers" / "Eight papers" removed from copy; redirects use JS + noscript as specified.
