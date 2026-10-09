# Contributing

```shell
uv sync
```

To use `poe` without activating `.venv` or prefixing it with `uv run`, install Poe once as a uv tool:

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

## Release

Bump the version in the PR with `poe patch`, `poe minor`, or `poe major`. CI fails if `[project].version` is not higher than on `main`.

After merge, tag `vX.Y.Z` on `main` (must match the project version) and push the tag. GitHub Actions publishes the sdist and wheel to PyPI using trusted publishing. Register this repository as a trusted publisher on PyPI before the first release.
