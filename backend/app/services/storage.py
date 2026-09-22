"""File storage helpers for uploaded documents."""

import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import Settings


def build_unique_filename(original_filename: str | None) -> str:
    """Return a UUID-based filename preserving the original extension when present."""
    suffix = Path(original_filename or "").suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


async def save_upload(file: UploadFile, settings: Settings) -> tuple[str, Path]:
    """
    Persist an uploaded file under temp/uploads/ with a unique UUID name.

    Returns:
        (stored_filename, absolute_path)
    """
    stored_name = build_unique_filename(file.filename)
    destination = settings.upload_dir / stored_name

    async with aiofiles.open(destination, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            await out_file.write(chunk)

    await file.close()
    return stored_name, destination.resolve()
