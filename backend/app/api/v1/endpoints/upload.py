"""Document upload and forensic analysis endpoint."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.schemas.analysis import AnalysisResult
from app.services.pipeline import DocumentAnalyzerPipeline
from app.services.storage import save_upload

router = APIRouter(tags=["analysis"])


@router.post(
    "/upload",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Upload and analyze a document",
)
async def upload_and_analyze_document(
    file: UploadFile = File(..., description="JPEG, PNG, or PDF document"),
    settings: Settings = Depends(get_settings),
) -> AnalysisResult:
    """
    Accept a document upload, persist it under ``temp/uploads/``, run the
    forensic pipeline, and return risk scoring plus static asset URLs.
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
    pipeline = DocumentAnalyzerPipeline(settings=settings)

    try:
        result = await run_in_threadpool(
            pipeline.run,
            saved_path,
            stored_filename=stored_name,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document analysis failed: {exc}",
        ) from exc

    return result
