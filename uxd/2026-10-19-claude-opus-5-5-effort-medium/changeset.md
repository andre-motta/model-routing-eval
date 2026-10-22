---
prototype_id: RHAISTRAT-1527
type: changeset
created_at: 2026-10-19T12:00:00Z
---

# Changeset: RHAISTRAT-1527

Standalone HTML prototype (PatternFly 6 CDN). No existing codebase modified.

## New Files

### Prototype (`.artifacts/RHAISTRAT-1527/prototype/`)
- `index.html`: Entry page linking to both screens and explaining `?scenario=`
- `playground.html`: Gen AI studio Playground with Settings card (model select, modality labels, audio transcription model dropdown) and Chat card (transcript, composer, per-modality Attach image / Attach audio controls)
- `ai-asset-endpoints.html`: AI asset endpoints table with Capabilities labels, Show filter, and Edit capabilities modal containing the Transcription endpoint (ASR) flag
- `assets/data.js`: Mock models (catalog tags `image-inferencing` / `audio-asr`), AI assets, MIME allowlist, 10 MB limit, sample image and generated WAV tone, scenario helper
- `assets/playground.js`: Scenario seeds (15), model-driven control visibility, client-side file validation (0 bytes, MIME, size), one-file-per-conversation limit, ASR blocking, staged upload/transcribe/respond progress, New chat reset
- `assets/endpoints.js`: Scenario seeds (6), table rendering, ASR flag modal with save feedback, filter
- `assets/app.css`: Layout for chat, composer, progress and table highlights on top of PF6 tokens
- `uxd-prototype-bar/*`: Prototype Bar runtime and config (installed by `install-prototype-bar.sh`)

### Artifacts (`.artifacts/RHAISTRAT-1527/`)
- `user-stories.json`: 8 user stories, 2 personas, AC mapping
- `journeys.json`: 5 journeys
- `scenarios.json`: 2 pages, 21 scenarios
- `metadata.json`, `prototype-summary.yaml`, `prototype-bar.json`, `changeset.md`

## Modified Files
- `rfe-snapshot.md`: frontmatter refreshed (`mode: skip`, `status: draft`, `iteration: 0`, `created_at`)
- `prototype/*.html`: Prototype Bar config and scripts injected before `</body>`
