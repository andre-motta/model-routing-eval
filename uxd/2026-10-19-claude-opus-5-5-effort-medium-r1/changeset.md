---
prototype_id: RHAISTRAT-1527
type: changeset
created_at: 2026-10-19T14:24:17Z
---

# Changeset: RHAISTRAT-1527

Standalone PatternFly 6 HTML prototype (CDN, no build). All paths are relative to `.artifacts/RHAISTRAT-1527/`.

## New Files

### Prototype (`prototype/`)
- `prototype/index.html`: Playground screen. Masthead, Gen AI studio nav, Settings card (model selector, supported-input labels, system instructions, temperature), chat card (transcript, composer with per-modality Image and Audio controls, transcription model dropdown, limits hint).
- `prototype/playground.js`: Playground behavior. Capability-driven controls (`supported_modalities`), client-side validation (10 MB, JPG/PNG, WAV/MP3, zero-byte) with no upload on failure, simulated upload to a file ID, image and audio (Uploading, Transcribing audio, Generating response) flows, one-file-per-conversation enforcement, New chat reset, and 12 `?scenario=` seeds.
- `prototype/ai-asset-endpoints.html`: AI asset endpoints screen shell.
- `prototype/assets.js`: AI asset endpoints table with Supported inputs and Use in Playground columns, a use filter, a row actions menu, and the Edit endpoint use modal (Chat or Transcription (ASR)). Includes 5 `?scenario=` seeds.
- `prototype/common.js`: Shared PF6 markup helpers (alert, label, spinner, helper text, menu toggle and menu), keyboard-accessible dropdown handling, inline SVG icons, mock model catalog, and ASR assets.
- `prototype/app.css`: Layout only (Playground grid, chat bubbles, composer, dropdown positioning). PatternFly supplies component styling.
- `prototype/uxd-prototype-bar/*`: Prototype Bar assets copied by `install-prototype-bar.sh` (bar runtime, CSS, scenario runtime, serializers, `prototype-bar.json`).

### Artifacts
- `user-stories.json`: 2 inferred personas, 8 user stories, 18 acceptance criteria.
- `journeys.json`: 4 journeys, 13 steps, with stable `data-ouia-component-id` selectors.
- `scenarios.json`: 2 pages, 17 scenarios (Playground 12, AI asset endpoints 5).
- `metadata.json`, `prototype-summary.yaml`, `prototype-bar.json`, `changeset.md`.

## Modified Files
- `rfe-snapshot.md`: frontmatter refreshed (`mode: skip`, `status: draft`, `iteration: 0`, `created_at`).
- `prototype/index.html`, `prototype/ai-asset-endpoints.html`: Prototype Bar config and scripts injected before `</body>` by `install-prototype-bar.sh`.
