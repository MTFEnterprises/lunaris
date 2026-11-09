# Contributing to LUNARIS

## Branches
- One feature per branch: `m<N>-<feature>`, for example `m2-illumination`, `m4-date-shift`.
- Branch from `main`, keep branches short-lived.

## Pull requests
- Small PRs. Fill the PR template.
- M1 reviews every PR. Squash merge only.
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
