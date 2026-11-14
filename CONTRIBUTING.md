# Contributing to LUNARIS

## Branches
- Name branches `feature/mN-short-name`, where N is the member number 1..5; for example `feature/m2-illumination`.
- Nobody pushes directly to `main`.
- Branch from `main`, keep branches short-lived.

## Pull requests
- Small PRs. Fill the PR template.
- Open every PR against `main`.
- Before opening a PR, run `git fetch origin && git merge origin/main`.
- M1 squash-merges after the Vercel check is green.
- `main` must stay deployable at all times.
- Tag the PR with the tier: `tier1`, `tier2`, `tier3`, `tier4`.

## Commit messages
Short and clear: `m3: add horizon mask for one site`.

## Shared files (ask M1 before changing)
- `docs/conventions.md`
- `docs/decisions.md`
- Data format v2 and API names

## Files that must NOT be committed
- DEM files, SPICE kernels (large). Commit a download script instead.
- `.env` files, API keys, secrets.
- `node_modules/`, `.venv/`, `__pycache__/`.

## Honesty rules
- Data classes: OBSERVED, PUBLISHED, CALCULATED, ESTIMATED, ILLUSTRATIVE, UNAVAILABLE.
- No fake data. Missing data is `UNAVAILABLE`.
- Never claim NASA approval or flight certification.

## Tests
- Every module ships with its own tests (analytic cases with known answers).
- M1 runs integration and acceptance tests; results go into `docs/test_report.md`.
