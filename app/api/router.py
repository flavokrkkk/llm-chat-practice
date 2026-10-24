from fastapi import APIRouter, Depends, Request
from app.api.v1.chat import router as chat_router
from app.api.v1.user import router as user_router
from app.api.v1.stats import router as stats_router

v1_router = APIRouter(prefix="/v1")


v1_router.include_router(chat_router, tags=["chats"], prefix="/chats")
v1_router.include_router(user_router, tags=["users"], prefix="/users")
v1_router.include_router(stats_router, tags=["stats"], prefix="/stats")
