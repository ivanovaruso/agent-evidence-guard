# Publishing to PyPI

Agent Evidence Guard is prepared for tokenless PyPI publication through GitHub Actions Trusted Publishing.

## Security model

The repository does **not** store a PyPI username, password, or long-lived API token.

Publishing is isolated in `.github/workflows/release.yml`:

1. a normal read-only job validates the release tag and builds the wheel/sdist;
2. the distributions are passed as a GitHub Actions artifact;
3. a separate `publish-pypi` job receives `id-token: write` only for the OIDC exchange with PyPI;
4. the publish job is bound to the GitHub environment named `pypi`.

## One-time PyPI configuration

Configure a PyPI **pending Trusted Publisher** for the project before the first PyPI upload.

Use these exact values:

- PyPI project name: `agent-evidence-guard`
- GitHub owner: `ivanovaruso`
- GitHub repository: `agent-evidence-guard`
- Workflow filename: `release.yml`
- Environment name: `pypi`

The workflow path in this repository is:

`.github/workflows/release.yml`

PyPI asks for the workflow **filename**, not the full path.

## GitHub environment

Create a repository environment named `pypi` before the first PyPI publication.

Recommended protection:

- restrict the environment to the release workflow when GitHub supports the rule;
- require maintainer approval for deployment if available for the repository/account plan;
- do not place PyPI API tokens in the environment.

## Release procedure

1. Ensure CI is green on `main`.
2. Update the package version and changelog through a reviewed PR.
3. Publish a GitHub Release with tag `v<package-version>`.
4. `.github/workflows/release.yml` verifies that the release tag exactly matches the version in `pyproject.toml`.
5. The build job produces wheel and source distribution artifacts.
6. The publish job uses PyPI Trusted Publishing to upload them.
7. Verify the new version on PyPI and test installation in a clean environment.

## Important boundaries

- Do not publish from an unreviewed branch.
- Do not add `workflow_dispatch` to the Trusted Publisher workflow merely for convenience.
- Do not add a long-lived `PYPI_TOKEN` secret while Trusted Publishing is available.
- Treat changes to `.github/workflows/release.yml` as security-sensitive.
- A GitHub Release is not evidence that PyPI publication succeeded; verify the PyPI project separately.
