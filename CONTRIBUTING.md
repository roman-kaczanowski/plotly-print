# Contributing

```shell
poe install
```

That runs `uv sync --all-groups` (dev and test). To use `poe` without activating `.venv` or prefixing it with `uv run`, install Poe once as a uv tool:

```shell
uv tool install poethepoet
```

Commit `uv.lock`. `poe hooks` installs git hooks (pre-push, post-checkout, post-merge).

```shell
poe check
poe check_docs
poe test
```

`poe format` and `poe format_docs` apply the same tools in write mode.

## Kaleido visual benchmark

Compare plotly-print to Kaleido (dev-only; not in the PyPI wheel). Kaleido is in the `test` dependency group and is installed by `poe install` / `uv sync`.

```shell
poe benchmark
```

Writes side-by-side PNGs (Kaleido / Chromium left, plotly-print / QuickJS right) and `benchmark_summary.json` under `assets/benchmarks/`, and refreshes the speed/visual sections in `README.md` (image links use absolute `raw.githubusercontent.com` URLs). Commit those assets with the README when timings or visuals change.

`poe test` includes a Kaleido mean-pixel-diff check for **every** chart fixture in `benchmark/cases.py` (skipped if Kaleido is not installed).

## Release

Bump the version in the PR with `poe patch`, `poe minor`, or `poe major`. CI fails if `[project].version` is not higher than on `main`.

After merge, tag `vX.Y.Z` on `main` (must match the project version) and push the tag. GitHub Actions publishes the sdist and wheel to PyPI using trusted publishing. Register this repository as a trusted publisher on PyPI before the first release.
