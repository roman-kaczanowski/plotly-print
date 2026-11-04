# Agent instructions

plotly-print: Python package + QuickJS micro-DOM for browser-less Plotly static export.

## Context, loaded on demand

- Package map and flow: `src/plotly_print/AGENTS.md` (auto-loaded there).
- JS and micro-DOM rules: `src/plotly_print/js/AGENTS.md` (auto-loaded there).
- Tests: `tests/AGENTS.md` (auto-loaded there).
- Coding standards: skill `project-standards` (load before changing code).
- Markdown: skill `markdown` (load before editing `.md`).

## Commands

`poe format` | `poe test` | `poe check` | `poe benchmark` | `poe format_docs`

After Python edits run `poe format`. After Markdown run `poe format_docs`.

## Non-negotiables

- Vendored `src/plotly_print/js/plotly_comprehensive_2d.js`: never open whole-file, never edit. Use capped shell `grep -o ... | head`.
- No new dependency outside `pyproject.toml` and the lockfile.
- Scratch under `.artifacts/` (gitignored); do not commit.
- ASCII only in identifiers, comments, and docs; no emojis.
