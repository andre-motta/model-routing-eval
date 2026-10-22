---
prototype_id: RHAISTRAT-1527
type: changeset
created_at: 2026-10-19T12:00:00Z
---

# Changeset: RHAISTRAT-1527

## New Files
- `prototype/index.html`: Playground page shell (model select, modality controls, chat transcript, composer)
- `prototype/ai-assets.html`: AI Asset Endpoints page shell (table, mark-as-ASR dialog)
- `prototype/app.js`: Mock data, `?scenario=` wiring, file validation, one-file-per-conversation limit, ASR progress flow
- `prototype/app.css`: Small layout additions on top of PatternFly 6
- `user-stories.json`, `journeys.json`, `scenarios.json`: Stories, 4 journeys, 8 + 3 on-load scenarios
- `metadata.json`, `prototype-summary.yaml`, `changeset.md`, `prototype-bar.json`

## Prototype Bar (added by install-prototype-bar.sh)
- `prototype/uxd-prototype-bar/*`: Bar runtime, CSS, scenario runtime, export serializers
- `prototype/index.html`, `prototype/ai-assets.html`: bar script and config injected before `</body>`

## Modified Files
- `rfe-snapshot.md`: unchanged (local source)
