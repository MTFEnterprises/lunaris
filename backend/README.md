# Backend

FastAPI app (Python 3.14). Owner: M1. M2 and M3 add their modules here.

Planned structure (created during the event, H1 onward):

```
main.py        FastAPI app, CORS, routers
schemas.py     pydantic request/response models
errors.py      common error format
provenance.py  data class and lineage
cache.py       in-memory and file cache
fallback/      labelled sample and cached scenarios
routers/       one file per endpoint group
services/      callers of M2 and M3 functions
assessment.py  pass / fail / unknown engine
report.py      report data assembly
tests/         pytest
```

M2 modules: `ephemeris.py`, `illumination.py`, `power.py`, `link.py`.
M3 modules: `terrain.py`, `horizon.py`, `slope.py`, `hazard.py`.

Note: code written before the event (14 to 15 Nov) is throwaway/learning code. Final code is written during the event.
