from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.audio import AudioFile
from app.schemas.audio import AudioUpdate # using placeholder schemas

class CRUDAudioFile(CRUDBase[AudioFile, AudioFile, AudioUpdate]): # placeholder schemas
    async def create_with_owner(
        self,
        db: AsyncSession,
        *,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        content_type: Optional[str],
        user_id: int,
    ) -> AudioFile:
        db_obj = AudioFile(
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            content_type=content_type,
            user_id=user_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_owner(self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100) -> List[AudioFile]:
        result = await db.execute(
            select(self.model)
            .filter(AudioFile.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

audio_file = CRUDAudioFile(AudioFile)