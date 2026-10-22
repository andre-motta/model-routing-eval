---
prototype_id: RHAISTRAT-1527
type: changeset
created_at: 2026-10-19T12:00:00Z
---

# Changeset: RHAISTRAT-1527

## New Files
- `prototype/playground.html`: Playground page: model selector, Text/Image/Audio input type, image dropzone, audio dropzone with ASR model dropdown, inline image rendering, one-per-conversation notice, and 7 scenario end-states
- `prototype/ai-assets.html`: AI Asset Endpoints table with ASR-capable flag and badge, plus 3 scenario end-states
- `user-stories.json`: 9 user stories derived from the RFE
- `journeys.json`: 3 journeys (image, audio via ASR, flag an ASR AI Asset)
- `scenarios.json`: 10 scenarios across 2 pages
- `metadata.json`: prototype metadata and assumptions
- `prototype-summary.yaml`: machine-readable summary
- `prototype-bar.json`: Prototype Bar config (synced from scenarios)
- `prototype/uxd-prototype-bar/`: Prototype Bar runtime installed by `install-prototype-bar.sh`

## Modified Files
- `prototype/playground.html`: Prototype Bar script injected by `install-prototype-bar.sh`
- `prototype/ai-assets.html`: Prototype Bar script injected by `install-prototype-bar.sh`
