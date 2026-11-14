"""Map layers for the frontend (M3's PNGs + layers.json). Owner: M1.

GET /api/layers              -> layers.json (projection, extent, pixel<->lat/lon formula)
GET /api/layers/{name}.png   -> one PNG from data/layers/ (same-origin, so the map needs no CORS)
"""
import json
import re

from fastapi import APIRouter
from fastapi.responses import FileResponse

import config
from errors import ErrorCode, LunarisError, ServiceUnavailable

router = APIRouter(prefix="/api", tags=["layers"])


class LayerNotFound(LunarisError):
    status_code = 404
    default_code = ErrorCode.NOT_FOUND


_NAME = re.compile(r"^[a-z0-9_]+\.png$")


@router.get("/layers", summary="Map layer catalogue (layers.json)")
def layers_catalogue():
    path = config.DATA_DIR / "layers.json"
    if not path.is_file():
        raise ServiceUnavailable("data/layers.json is not present.", {"file": "layers.json"})
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/layers/{name}", summary="One map layer PNG", response_class=FileResponse)
def layer_png(name: str):
    path = config.DATA_DIR / "layers" / name
    if not _NAME.match(name) or not path.is_file():
        raise LayerNotFound(f"Layer '{name}' not found.", {"name": name})
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})
