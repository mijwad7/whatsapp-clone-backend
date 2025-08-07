from fastapi import APIRouter

router = APIRouter()

@router.post("/webhook")
async def webhook_endpoint():
    return {"status": "received"}