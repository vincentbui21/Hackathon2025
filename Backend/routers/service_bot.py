from fastapi import APIRouter
from pydantic import BaseModel
from app.database import get_connection

from AI2_LLM_model.models.main import (
    get_product_recommendation,
    mention_missing_products,
    talk_to_customer_service
)

router = APIRouter(prefix="/service", tags=["Service Bot"])


class ProductRequest(BaseModel):
    product_id: int

class MissingItemsRequest(BaseModel):
    product_id: int
    amount_missing: int
    order_id: str

class CustomerMessageRequest(BaseModel):
    customer_message: str
    reset: bool = False


# -------------- Shared helper: fetch product + alternatives --------------
def fetch_alternative_products(product_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM Product
        WHERE ProductID = %s;
    """, (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        connection.close()
        return None, [], None

    # Call LLM
    raw = get_product_recommendation(product_id)

    # Extract the LLM explanation
    llm_explanation = None
    alternatives = []

    if isinstance(raw, dict):
        options = raw.get("Options", [])
        llm_explanation = raw.get("Answers", None)

        # Check if Options contains full product objects or just IDs
        if options and isinstance(options[0], dict):
            # LLM returned full product objects - extract IDs and fetch from DB
            ids = [int(opt.get("id", 0)) for opt in options if opt.get("id")]
        else:
            # LLM returned just IDs
            ids = [
                int(x) for x in options
                if isinstance(x, int) or (isinstance(x, str) and x.isdigit())
            ]

        # Fetch alternative product details from database
        if ids:
            # Create placeholders for parameterized query
            placeholders = ', '.join(['%s'] * len(ids))
            cursor.execute(f"""
                SELECT *
                FROM Product
                WHERE ProductID IN ({placeholders});
            """, ids)
            alternatives = cursor.fetchall()

    cursor.close()
    connection.close()
    return product, alternatives, llm_explanation


# --------------------- /alternative ---------------------
@router.post("/alternative")
def get_product_and_alternatives(request: ProductRequest):
    product, alternatives, llm_response = fetch_alternative_products(request.product_id)

    if not product:
        return {"error": "Product not found"}

    return {
        "product": product,
        "alternatives": alternatives,
        "llm_response": llm_response
    }


# --------------------- /missing ---------------------
@router.post("/missing")
def handle_missing_product(request: MissingItemsRequest):

    # 1. get LLM apology + compensation + recs
    llm_response = mention_missing_products(
        product_id=request.product_id,
        amount_missing=request.amount_missing,
        order_id=request.order_id
    )

    # 2. fetch actual product + alt products from DB
    product, alternatives, _ = fetch_alternative_products(request.product_id)

    if not product:
        return {"error": "Product not found"}

    return {
        "product": product,
        "alternatives": alternatives,
        "llm_response": llm_response
    }


# --------------------- /talk ---------------------
@router.post("/talk")
def talk_to_service_bot(request: CustomerMessageRequest):

    response = talk_to_customer_service(
        customer_message=request.customer_message,
        conversation_delete=request.reset
    )

    return response
