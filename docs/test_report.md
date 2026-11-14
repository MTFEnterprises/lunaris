# Test Report

## Backend (pytest)
| # | Required test | Real test function | Status |
|---|---|---|---|
| 1 | Latitude 95 returns 400 | `backend/tests/test_api.py::test_lat_95_gives_400_invalid_coordinate` | PASS |
| 2 | Invalid date returns 400 | `backend/tests/test_api.py::test_bad_date_gives_400` | PASS |
| 3 | Empty scenario returns 400 | `backend/tests/test_api.py::test_empty_compare_scenarios_is_clear_error` | PASS |
| 4 | Unknown site returns 404 | `backend/tests/test_api.py::test_site_not_found_404` | PASS |
| 5 | M2/M3 failure returns 503 (mock) | `backend/tests/test_api.py::test_module_failure_gives_503` | PASS |
| 6 | Timeout and retry returns 503 | `backend/tests/test_api.py::test_timeout_retries_then_503` | PASS |
| 7 | Cache hit returns `cached: true` | `backend/tests/test_api.py::test_second_identical_request_is_cached` | PASS |
| 8 | Missing data makes assessment unknown | `backend/tests/test_api.py::test_assessment_missing_terrain_is_unknown_not_pass` | PASS |
| 9 | Thermal returns 501 and `UNAVAILABLE` | `backend/tests/test_api.py::test_thermal_is_501_unavailable` | PASS |
| 10 | `/api/openapi.json` returns 200 | `backend/tests/test_api.py::test_openapi_opens` | PASS |

## Total pytest result

Run: `backend\venv\Scripts\python.exe -m pytest backend -q`
Result: **122 passed, 3 skipped, 1 warning**

Date: 2026-11-14
Git commit: `7abc419f200f012ab8a034889da8699c6e99a6ad`
