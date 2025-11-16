from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from AI2_LLM_model.models.main import talk_to_customer_service, mention_missing_products, get_product_recommendation
from AI2_LLM_model.models.model1 import delete_history

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessageRequest(BaseModel):
    message: str
    conversation_delete: bool = False


class ChatMessageResponse(BaseModel):
    Answers: str
    Options: list[int] | None = None


@router.post("/message", response_model=ChatMessageResponse)
def send_message(request: ChatMessageRequest):
    """
    Send a message to the customer service chatbot.

    Args:
        request: ChatMessageRequest containing the user's message and optional conversation_delete flag

    Returns:
        ChatMessageResponse with AI's answer and optional product recommendations
    """
    try:
        response = talk_to_customer_service(
            customer_message=request.message,
            conversation_delete=request.conversation_delete
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")


@router.post("/clear")
def clear_conversation():
    """
    Clear the conversation history.

    Returns:
        Status message confirming conversation was cleared
    """
    try:
        delete_history()
        return {"status": "cleared", "message": "Conversation history has been deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")


class OrderApologyRequest(BaseModel):
    product_id: int
    amount_missing: int


@router.post("/order-apology", response_model=ChatMessageResponse)
def order_apology(request: OrderApologyRequest):
    """
    Trigger apology message for failed order validation with missing products.
    This uses the LLM to generate an apology and suggest alternative products.

    Args:
        request: OrderApologyRequest with product_id and amount_missing

    Returns:
        ChatMessageResponse with apology message and product alternatives
    """
    try:
        response = mention_missing_products(
            product_id=request.product_id,
            amount_missing=request.amount_missing
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order apology service error: {str(e)}")
