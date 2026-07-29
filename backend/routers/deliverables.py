from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from backend.services.deliverable_service import artifact_preview, export_deliverable, preview_deliverable
from backend.auth import get_current_user
from fastapi import Depends
from pydantic import BaseModel, Field

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


class PreviewBody(BaseModel):
    title: str = "Deliverable"
    reply: str = ""
    artifacts: list[str] = Field(default_factory=list)


@router.post("/preview")
def deliverable_preview(body: PreviewBody, _: str = Depends(get_current_user)) -> dict:
    return preview_deliverable(title=body.title, reply=body.reply, artifacts=body.artifacts)


@router.get("/artifact")
def single_artifact_preview(path: str, _: str = Depends(get_current_user)) -> dict:
    doc = artifact_preview(path)
    if not doc:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return doc


@router.post("/export")
def deliverable_export(body: PreviewBody, format: str = Query("pdf"), _: str = Depends(get_current_user)) -> Response:
    doc = preview_deliverable(title=body.title, reply=body.reply, artifacts=body.artifacts)
    data, media, filename = export_deliverable(doc, format.lower())
    return Response(content=data, media_type=media, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
