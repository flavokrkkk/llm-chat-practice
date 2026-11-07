from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/debug/boom")
async def boom() -> None:
    raise RuntimeError("boom")
