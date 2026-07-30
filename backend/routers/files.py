from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from backend.auth import get_current_user
from backend.config import settings
from backend.services.founder_files import is_founder_visible_file

router = APIRouter(prefix="/files", tags=["files"])

ALLOWED_SUFFIXES = {".md", ".json", ".csv", ".pdf", ".docx", ".xlsx", ".html", ".jsonl"}


@router.get("")
def list_files(_: str = Depends(get_current_user)) -> dict:
    rows = []
    root = settings.outputs_root
    if not root.exists():
        return {"files": rows}
    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in ALLOWED_SUFFIXES
        and "__pycache__" not in path.parts
        and is_founder_visible_file(path)
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for path in files[:80]:
        stat = path.stat()
        rows.append(
            {
                "name": path.name,
                "folder": path.parent.name,
                "type": path.suffix.lower().lstrip("."),
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "path": str(path.relative_to(settings.app_root)).replace("\\", "/"),
            }
        )
    return {"files": rows}


@router.get("/download")
def download_file(path: str, _: str = Depends(get_current_user)):
    file_path = (settings.app_root / path).resolve()
    if not str(file_path).startswith(str(settings.app_root.resolve())):
        return {"error": "Invalid path"}
    if not file_path.exists() or not file_path.is_file():
        return {"error": "File not found"}
    return FileResponse(file_path, filename=file_path.name)
