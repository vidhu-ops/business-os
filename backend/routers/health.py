from __future__ import annotations

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        content={
            "status": "ok",
            "service": "iidatech-api",
            "git": (os.getenv("RENDER_GIT_COMMIT") or "").strip(),
            "repo": (os.getenv("RENDER_GIT_REPO_SLUG") or "").strip(),
        },
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )