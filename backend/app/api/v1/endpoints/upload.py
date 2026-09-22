"""Document upload endpoint."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import Settings, get_settings
from app.schemas.upload import UploadResponse
from app.services.storage import save_upload

router = APIRouter(tags=["upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an identity / document file",
)
async def upload_document(
    file: UploadFile = File(..., description="JPEG, PNG, or PDF document"),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    """
    Accept a single file upload, validate MIME type, and store it securely
    under ``temp/uploads/`` with a UUID filename.
    """
    content_type = (file.content_type or "").lower()

    if content_type not in settings.allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{content_type}'. "
                f"Allowed: {', '.join(settings.allowed_content_types)}"
            ),
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    stored_name, saved_path = await save_upload(file, settings)

    return UploadResponse(
        status="success",
        filename=stored_name,
        original_filename=file.filename,
        path=str(saved_path),
        content_type=content_type,
    )
