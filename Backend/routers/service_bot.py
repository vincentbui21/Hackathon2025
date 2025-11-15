from fastapi import APIRouter

router = APIRouter(prefix="/service", tags=["Service Bot"])

@router.post("/chat")
async def chat_with_bot(message: str, order_id: str):
    # Forward message to AI agent 2
    return {
        "reply": "Suggested alternative: ...",
        "order_id": order_id
    }
