import os
import uuid
import aiofiles
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
import pathlib

from app import crud, models, schemas
from app.deps import get_db, get_current_active_user
from app.core.config import settings

router = APIRouter()

# ensure upload directory exists
UPLOAD_DIR = pathlib.Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    # remove potentially unsafe characters, keep extension
    base, ext = os.path.splitext(filename)
    # replace spaces, slashes, etc. with underscore
    safe_base = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in base)
    # limit length
    safe_base = safe_base[:100]
    return f"{safe_base}{ext}"

@router.post("/upload", response_model=schemas.Audio, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    file: UploadFile = File(..., description="The audio file to upload"),
    file_name: Optional[str] = Form(None, description="Optional custom name for the file")
):
    """
    Uploads an audio file for the current user.
    User can optionally provide a 'file_name' in the form data.
    """
    # validate file type 
    allowed_content_types = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/aac", "audio/flac"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_content_types)}"
        )

    original_filename = file_name or file.filename # use provided name or original filename
    if not original_filename:
         raise HTTPException(status_code=400, detail="File name must be provided either via form or filename.")

    sanitized_original = sanitize_filename(original_filename)

    # create a unique filename for storage to avoid conflicts
    _, ext = os.path.splitext(file.filename or "audio")
    stored_filename = f"{uuid.uuid4()}{ext}"

    # define the relative path for storage (e.g., user_id/stored_filename)
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True) # Ensure user-specific dir exists
    relative_file_path = pathlib.Path(str(current_user.id)) / stored_filename
    full_file_path = UPLOAD_DIR / relative_file_path

    try:
        # save the file
        async with aiofiles.open(full_file_path, "wb") as out_file:
            while content := await file.read(1024 * 1024): # read chunk by chunk (1MB)
                await out_file.write(content)
    except Exception as e:
        print(f"Error saving file: {e}")
        if full_file_path.exists():
             full_file_path.unlink() # delete the file if save failed
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    finally:
         await file.close() # ensure file handle is closed

    # create DB record
    audio_in_db = await crud.audio_file.create_with_owner(
        db=db,
        original_filename=sanitized_original, # store the sanitized name
        stored_filename=stored_filename, # store the unique name used on disk
        file_path=str(relative_file_path), # store relative path
        content_type=file.content_type,
        user_id=current_user.id,
    )

    return audio_in_db


@router.get("/", response_model=List[schemas.Audio])
async def list_user_audio_files(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get a list of audio files uploaded by the current user.
    Returns original filename and the relative path for reference.
    """
    audio_files = await crud.audio_file.get_multi_by_owner(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return audio_files

@router.get("/{audio_id}", response_model=schemas.Audio)
async def get_audio_file_info(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    audio_id: int
):
    """Get details of a specific audio file owned by the current user."""
    audio = await crud.audio_file.get(db=db, id=audio_id)
    if not audio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")
    if audio.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")
    return audio

@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audio_file(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    audio_id: int
):
    """Delete an audio file owned by the current user (record and file on disk)."""
    audio = await crud.audio_file.get(db=db, id=audio_id)
    if not audio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")
    if audio.user_id != current_user.id and not current_user.is_superuser: # only superusers can delete others' files
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this file")

    # delete file from disk
    full_file_path = UPLOAD_DIR / audio.file_path
    try:
         if full_file_path.is_file():
             full_file_path.unlink()
    except Exception as e:
         print(f"Error deleting file {full_file_path}: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not delete file from storage: {e}")

    # delete DB record
    await crud.audio_file.remove(db=db, id=audio_id)

    return None