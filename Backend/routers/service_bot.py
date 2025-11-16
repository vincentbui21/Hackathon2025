from fastapi import APIRouter
from pydantic import BaseModel
from app.database import get_connection

# Import the recommendation function
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

@router.post("/alternative")
def get_product_and_alternatives(request: ProductRequest):
    product_id = request.product_id

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # 1. Get main product information
    cursor.execute("""
        SELECT *
        FROM Product
        WHERE ProductID = %s;
    """, (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        connection.close()
        return {"error": "Product not found"}

    # 2. Get recommended alternative product IDs from your LLM
    recommended_ids = get_product_recommendation(product_id)
    
    # Ensure we have a list of product IDs
    if isinstance(recommended_ids, dict) and "Options" in recommended_ids:
        recommended_ids = recommended_ids["Options"]

    # 3. Fetch full product info for each recommended product
    if recommended_ids:
        format_ids = tuple(recommended_ids)
        if len(format_ids) == 1:
            format_ids = (format_ids[0],)
        query = f"""
            SELECT *
            FROM Product
            WHERE ProductID IN {format_ids};
        """
        cursor.execute(query)
        alternatives = cursor.fetchall()
    else:
        alternatives = []

    cursor.close()
    connection.close()

    return {
        "product": product,
        "alternatives": alternatives
    }

@router.post("/missing")
def handle_missing_product(request: MissingItemsRequest):

    response = mention_missing_products(
        product_id=request.product_id,
        amount_missing=request.amount_missing,
        order_id=request.order_id
    )

    return response

@router.post("/talk")
def talk_to_service_bot(request: CustomerMessageRequest):

    response = talk_to_customer_service(
        customer_message=request.customer_message,
        conversation_delete=request.reset
    )

    return response
