---
prototype_id: RHAISTRAT-1527
type: changeset
created_at: 2026-10-19T12:00:00Z
---

# Changeset: RHAISTRAT-1527

## New Files
- `prototype/index.html`: Redirects to the Playground
- `prototype/playground.html`: Playground page with model selector, capability labels, per-modality attach controls, ASR model dropdown, chat transcript
- `prototype/playground.js`: Playground logic: capability-driven controls, client-side validation (type, zero-byte, 10 MB), one-file-per-conversation limit, staged processing status, `?scenario=` seeds
- `prototype/ai-asset-endpoints.html`: AI Asset Endpoints table with ASR/transcription capability label and "Edit capabilities" modal
- `prototype/shared.css`: Layout and chat styling
- `prototype/uxd-prototype-bar/`: Prototype Bar and scenario runtime (installed by `install-prototype-bar.sh`)

## Artifacts
- `user-stories.json`, `journeys.json`, `scenarios.json`, `metadata.json`, `prototype-summary.yaml`, `prototype-bar.json`
