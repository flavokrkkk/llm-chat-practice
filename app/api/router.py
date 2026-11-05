from fastapi import APIRouter, Depends

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.stats import router as stats_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.user import router as user_router

from .dependencies.dependencies import get_current_user

v1_router = APIRouter(prefix="/v1")

PROTECTED = Depends(get_current_user)


@v1_router.get("/health")
async def health():
    return {"status": "ok"}


v1_router.include_router(auth_router, tags=["auth"], prefix="/auth")
v1_router.include_router(
    chat_router, tags=["chats"], prefix="/chats", dependencies=[PROTECTED]
)
v1_router.include_router(
    user_router, tags=["users"], prefix="/users", dependencies=[PROTECTED]
)
v1_router.include_router(
    stats_router, tags=["stats"], prefix="/stats", dependencies=[PROTECTED]
)
v1_router.include_router(
    transfers_router, tags=["transfers"], prefix="/transfers", dependencies=[PROTECTED]
)
