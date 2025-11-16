from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from AI2_LLM_model.models.main import talk_to_customer_service, mention_missing_products, get_product_recommendation
from AI2_LLM_model.models.model1 import delete_history

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessageRequest(BaseModel):
    message: str
    conversation_delete: bool = False


class ProductOption(BaseModel):
    id: int
    name: str
    price: float
    score: float


class ChatMessageResponse(BaseModel):
    Answers: str
    Options: list[int | ProductOption] | None = None


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
        print(f"🤖 Generating apology for product_id={request.product_id}, amount_missing={request.amount_missing}")

        response = mention_missing_products(
            product_id=request.product_id,
            amount_missing=request.amount_missing
        )

        print(f"📤 LLM Response: {response}")

        # Ensure response has the correct structure
        if not isinstance(response, dict):
            response = {"Answers": str(response), "Options": None}

        # If no Answers field, provide a default message
        if "Answers" not in response or not response["Answers"]:
            response["Answers"] = "I apologize for the inconvenience with your order. We detected a discrepancy in your delivery. Let me help you find suitable alternatives."

        # If no options are returned or options is empty, add a fallback message
        if not response.get("Options") or len(response.get("Options", [])) == 0:
            response["Answers"] = "I apologize for the inconvenience with your order. Unfortunately, I don't have any alternative products to recommend at this time. Please contact our customer service for further assistance."
            response["Options"] = None

        print(f"✅ Final response: Answers={response.get('Answers')[:100] if response.get('Answers') else 'None'}..., Options count={len(response.get('Options', []) or [])}")

        return response
    except Exception as e:
        print(f"❌ Error in order_apology: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Order apology service error: {str(e)}")
