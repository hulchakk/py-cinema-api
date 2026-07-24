from fastapi import APIRouter

router = APIRouter(
    prefix="/movies",
)


@router.get("")
async def movies():
    return {"message": "Movies"}
