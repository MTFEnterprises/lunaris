# Test Report

## Backend (pytest)
| # | Test | Status |
|---|---|---|
| 1 | Invalid latitude (95) returns 400 INVALID_COORDINATE | |
| 2 | Invalid date returns 400 | |
| 3 | Empty scenario returns clear error | |
| 4 | Site not found returns 404 | |
| 5 | M2/M3 function failure returns 503 (mocked) | |
| 6 | Timeout then retry then 503 | |
| 7 | Repeat request returns cached = true | |
| 8 | Assessment returns unknown when data is missing | |
| 9 | Thermal endpoint returns 501 and UNAVAILABLE | |
| 10 | /openapi.json opens | |

## Acceptance checklist
- [ ] App opens and navigation works
- [ ] Lunar site selectable
- [ ] Date and time selectable
- [ ] Sun information scientifically correct
- [ ] Earth information scientifically correct
- [ ] Geometric and terrain-corrected visibility shown separately
- [ ] At least 3 scenarios compare
- [ ] Timeline usable
- [ ] Terrain analysis (where data exists)
- [ ] Sources and limitations shown
- [ ] Missing data shown honestly as UNAVAILABLE
- [ ] Report generates
- [ ] No critical errors
- [ ] Demo complete and understandable

## Gates
| Gate | When | Result |
|---|---|---|
| Gate 1 | H12: one site, one date, sky view and metrics live | |
| Gate 2 | H24: Tier 1 complete | |
| Gate 3 | H38: Tier 2 complete, feature freeze | |
