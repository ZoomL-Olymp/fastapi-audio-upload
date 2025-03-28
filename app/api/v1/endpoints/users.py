from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.deps import get_db, get_current_active_user, get_current_active_superuser

router = APIRouter()

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)) -> Any:
    """
    Get current user.
    """
    return current_user

@router.put("/me", response_model=schemas.User)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserUpdate, # allow updating specific fields
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update own user. Only non-sensitive fields allowed.
    """
    # filter out potentially sensitive fields
    update_data = user_in.model_dump(exclude_unset=True, exclude={"is_superuser", "is_active"}) # Example filter
    if not update_data:
         raise HTTPException(status_code=400, detail="No update data provided or only restricted fields attempted.")

    user = await crud.user.update(db=db, db_obj=current_user, obj_in=update_data)
    return user

# --- superuser endpoints ---

@router.get("/", response_model=List[schemas.User], dependencies=[Depends(get_current_active_superuser)])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve users (Superuser only).
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.User, dependencies=[Depends(get_current_active_superuser)])
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific user by ID (Superuser only).
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.User, dependencies=[Depends(get_current_active_superuser)])
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    user_in: schemas.UserUpdate, # superuser can update more fields
) -> Any:
    """
    Update a user (Superuser only).
    """
    user = await crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    # allow superuser to update all fields defined in UserUpdate
    user = await crud.user.update(db=db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}", response_model=schemas.User, dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
) -> Any:
    """
    Delete a user (Superuser only).
    Consider implications: what happens to their audio files? Mark inactive instead?
    For now, we delete the user record. Files remain on disk unless cleaned up separately.
    """
    user_to_delete = await crud.user.get(db=db, id=user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    if user_to_delete.is_superuser:
         raise HTTPException(status_code=403, detail="Superusers cannot be deleted this way")
    deleted_user = await crud.user.remove(db=db, id=user_id)
    if not deleted_user:
         raise HTTPException(status_code=404, detail="User not found during delete attempt")
    return deleted_user # return the deleted user info