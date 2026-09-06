import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from slugify import slugify

from app.core.config import settings


def validate_and_save_image(file: UploadFile, subfolder: str = "complaints") -> tuple[str, str, int]:
    """
    Validates extension + size, writes the file under UPLOAD_DIR/<subfolder>/
    with a random, collision-proof filename (never trusts the client-supplied
    filename), and returns (relative_path, original_filename, size_bytes).
    """
    original_name = file.filename or "upload"
    ext = Path(original_name).suffix.lower()

    if ext not in settings.allowed_image_extensions_list:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.allowed_image_extensions_list)}",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = file.file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )
    if len(contents) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty.")

    safe_stem = slugify(Path(original_name).stem)[:60] or "image"
    secure_filename = f"{safe_stem}-{uuid.uuid4().hex[:12]}{ext}"

    target_dir = Path(settings.UPLOAD_DIR) / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / secure_filename

    with open(target_path, "wb") as f:
        f.write(contents)

    relative_path = f"{subfolder}/{secure_filename}"
    return relative_path, original_name, len(contents)
