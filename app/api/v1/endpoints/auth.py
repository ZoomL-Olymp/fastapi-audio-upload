import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core import security
from app.crud import user as crud_user
from app.schemas.token import Token
from app.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()

YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USERINFO_URL = "https://login.yandex.ru/info"

@router.get("/login/yandex")
async def login_yandex():
    """
    Redirects the user to Yandex for authentication.
    """
    redirect_uri = settings.YANDEX_REDIRECT_URI
    auth_url = (
        f"{YANDEX_AUTH_URL}?response_type=code&client_id={settings.YANDEX_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
    )
    return RedirectResponse(url=auth_url)

@router.get("/yandex/callback")
async def yandex_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """
    Handles the callback from Yandex after user authentication.
    Exchanges the code for a token, fetches user info, creates/updates user,
    and returns internal JWT tokens.
    """
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.YANDEX_CLIENT_ID,
        "client_secret": settings.YANDEX_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        try:
            # 1. Exchange code for Yandex token
            token_response = await client.post(YANDEX_TOKEN_URL, data=token_data)
            token_response.raise_for_status() # raise exception for non-2xx responses
            yandex_token_info = token_response.json()
            yandex_access_token = yandex_token_info.get("access_token")

            if not yandex_access_token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not get Yandex access token")

            # 2. Fetch user info from Yandex
            headers = {"Authorization": f"OAuth {yandex_access_token}"}
            user_info_response = await client.get(YANDEX_USERINFO_URL, headers=headers)
            user_info_response.raise_for_status()
            yandex_user_info = user_info_response.json()

            yandex_id = yandex_user_info.get("id")
            email = yandex_user_info.get("default_email")
            first_name = yandex_user_info.get("first_name")
            last_name = yandex_user_info.get("last_name")

            if not yandex_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not get Yandex user ID")

        except httpx.HTTPStatusError as e:
            # log the error details e.response.text
            print(f"HTTP Error contacting Yandex: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Error communicating with Yandex: {e.response.status_code}")
        except Exception as e:
            # log generic error
            print(f"Generic error during Yandex auth: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during Yandex authentication")

    # 3. Check if user exists in DB
    user = await crud_user.get_by_yandex_id(db, yandex_id=yandex_id)

    if not user:
        # determine if the first user should be superuser
        is_superuser = False
        if settings.FIRST_SUPERUSER_YANDEX_ID and settings.FIRST_SUPERUSER_YANDEX_ID == yandex_id:
             is_superuser = True
        # 4. Create new user if not exists
        user = await crud_user.create_with_yandex(
            db=db,
            yandex_id=yandex_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_superuser=is_superuser
        )
    else:
        # update user info if it changed in Yandex
        update_data = {}
        if email and user.email != email:
            update_data["email"] = email
        if first_name and user.first_name != first_name:
            update_data["first_name"] = first_name
        if last_name and user.last_name != last_name:
            update_data["last_name"] = last_name
        if update_data:
            user = await crud_user.update(db=db, db_obj=user, obj_in=update_data)


    # 5. Generate internal JWT tokens
    access_token = security.create_access_token(subject=user.id, yandex_id=user.yandex_id)
    refresh_token = security.create_refresh_token(subject=user.id, yandex_id=user.yandex_id)

    # 6. Return tokens
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh-token", response_model=Token)
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Refreshes the access token using a valid refresh token.
    Expects refresh token in the Authorization header: "Bearer <refresh_token>"
    or potentially in the request body. Let's stick to header for consistency.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Missing or invalid Authorization header",
             headers={"WWW-Authenticate": "Bearer"},
         )
    token = auth_header.split(" ")[1]

    token_data = security.decode_token(token)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token_data or not token_data.refresh: # must be a refresh token
        raise credentials_exception

    user = await crud_user.get(db, id=int(token_data.sub))
    if not user or not user.is_active:
        raise credentials_exception # user not found or inactive

    # check if Yandex ID in token matches user's current Yandex ID
    if token_data.yandex_id != user.yandex_id:
         print(f"Yandex ID mismatch: Token {token_data.yandex_id}, User {user.yandex_id}")
         raise credentials_exception

    # Issue new tokens
    new_access_token = security.create_access_token(subject=user.id, yandex_id=user.yandex_id)
    new_refresh_token = security.create_refresh_token(subject=user.id, yandex_id=user.yandex_id) # Issue a new refresh token as well

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)

# endpoint to test authentication
@router.get("/test-auth", response_model=str)
async def test_auth(current_user: User = Depends(get_current_active_user)):
    """Tests if the user is authenticated."""
    return f"Hello, authenticated user {current_user.email or current_user.yandex_id}!"