from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.core.security import require_any_role

router = APIRouter(prefix="/api/upload", tags=["Upload"])

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOC_TYPES = {"application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = "erp",
    current_user=Depends(require_any_role),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    if not settings.CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=503, detail="File storage not configured")

    try:
        result = cloudinary.uploader.upload(
            content,
            folder=f"erp/{folder}",
            resource_type="image",
        )
        return {"url": result["secure_url"], "public_id": result["public_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    folder: str = "documents",
    current_user=Depends(require_any_role),
):
    if file.content_type not in ALLOWED_DOC_TYPES | ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and image files are allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    if not settings.CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=503, detail="File storage not configured")

    try:
        resource_type = "raw" if file.content_type == "application/pdf" else "image"
        result = cloudinary.uploader.upload(
            content,
            folder=f"erp/{folder}",
            resource_type=resource_type,
        )
        return {"url": result["secure_url"], "public_id": result["public_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
