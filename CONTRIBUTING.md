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

Compare plotly-print output to Kaleido side by side (not part of the PyPI wheel). Kaleido is in the `test` dependency group and is installed by `poe install` / `uv sync`.

```shell
poe benchmark_quick
```

Full gallery (all chart fixtures): `poe benchmark`.

Outputs are written to `.artifacts/benchmark/` (`report.md`, PNGs, `benchmark_summary.json`).

## Release

Bump the version in the PR with `poe patch`, `poe minor`, or `poe major`. CI fails if `[project].version` is not higher than on `main`.

After merge, tag `vX.Y.Z` on `main` (must match the project version) and push the tag. GitHub Actions publishes the sdist and wheel to PyPI using trusted publishing. Register this repository as a trusted publisher on PyPI before the first release.
