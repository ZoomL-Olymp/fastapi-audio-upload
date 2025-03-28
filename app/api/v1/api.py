from fastapi import APIRouter
from .endpoints import auth#, users, audio

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(audio.router, prefix="/audio", tags=["audio"])