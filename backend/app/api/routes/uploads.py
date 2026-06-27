"""Image uploads for product photos (Admin/Staff only).

Files are written to settings.UPLOAD_DIR and served back under /uploads/<name>.
In Docker that directory is a mounted volume so images survive restarts.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import require_admin
from app.core.config import settings
from app.models.user import User

router = APIRouter()

ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED))}.",
        )
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File too large (max {settings.MAX_UPLOAD_MB} MB).",
        )
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (upload_dir / name).write_bytes(data)
    return {"url": f"/uploads/{name}", "filename": name}
