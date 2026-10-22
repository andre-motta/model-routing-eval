---
prototype_id: RHAISTRAT-1527
type: changeset
created_at: 2026-10-19T14:30:27.129561+00:00
---

# Changeset

Created a PatternFly 6 standalone Playground and AI Asset Endpoints page. Added model capability controls, file validation, image previews, ASR endpoint registration, simulated upload/transcription progress, text responses and conversation reset.

## Files created

- `changeset.md`
- `journeys.json`
- `metadata.json`
- `prototype-bar.json`
- `prototype-summary.yaml`
- `prototype/app.js`
- `prototype/endpoints.html`
- `prototype/index.html`
- `prototype/style.css`
- `prototype/uxd-prototype-bar/export-pf-spec.browser.js`
- `prototype/uxd-prototype-bar/prototype-bar-standalone.js`
- `prototype/uxd-prototype-bar/prototype-bar.css`
- `prototype/uxd-prototype-bar/prototype-bar.json`
- `prototype/uxd-prototype-bar/serialize-page.browser.js`
- `prototype/uxd-prototype-bar/uxd-scenario-runtime.js`
- `reachability-check.json`
- `scenarios.json`
- `user-stories.json`

## Modified

- `rfe-snapshot.md`: normalized required frontmatter; source content preserved.

## Validation

- JavaScript syntax check passed.
- Static reachability check passed for 2 routes, 3 journeys, 10 scenarios, action selectors and local links.
- Prototype Bar installer completed for both HTML pages.
- Browser visual verification unavailable: browser tool reported `Browser is not available: iab`; Playwright is not installed.
- Backend calls, storage, model registry, inference timing and accessibility scan remain unverified. The prototype simulates these interactions.

## Run

Serve `prototype/` with a static HTTP server. Entry point: `index.html`. Select conditions using the Prototype Bar Scenario menu or `?scenario=<id>`. No exports or publication requested.
