Run the uxd-prototype-create skill from the uxd-prototype plugin. In Claude Code it is the slash command `/uxd-prototype:uxd-prototype-create`; in Codex it is the skill staged under `.agents/skills/uxd-prototype-create`. Invoke it with exactly these arguments:

    https://redhat.atlassian.net/browse/RHAISTRAT-1527 --workspace standalone --target none --decisions skip

This is a non-interactive run. Treat this message as the user's "yes" to the Prototype Plan and to every later confirmation the skill would normally wait for; print the plan and continue without stopping. Jira is not reachable from this environment: the RFE is already saved as the local artifact `.artifacts/RHAISTRAT-1527/rfe-snapshot.md`, so use it as the source (the skill's Step 1 local-artifact path).

Complete every step the skill defines for a standalone prototype: user stories, `journeys.json`, `scenarios.json` (distinct on-load end states per page, selectable with `?scenario=<id>`), the PatternFly 6 standalone HTML prototype under `.artifacts/RHAISTRAT-1527/prototype/`, the reachability self-check, `changeset.md`, `metadata.json`, `prototype-summary.yaml`, and the Prototype Bar install. Finish with the skill's summary of what was built.
