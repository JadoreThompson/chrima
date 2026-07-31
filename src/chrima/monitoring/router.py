from fastapi import APIRouter

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def get_healthcheck():
    return {"status": "ok"}
