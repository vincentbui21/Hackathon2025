from fastapi import APIRouter
from pydantic import BaseModel
from app.database import get_connection

# Import the recommendation function
from AI2_LLM_model.models.main import get_product_recommendation

router = APIRouter(prefix="/service", tags=["Service Bot"])


class ProductRequest(BaseModel):
    product_id: int


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
