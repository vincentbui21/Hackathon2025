from fastapi import APIRouter
from pydantic import BaseModel
from app.database import get_connection

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

    # 2. Get 3 random alternative products
    cursor.execute("""
        SELECT *
        FROM Product
        WHERE ProductID != %s
        ORDER BY RAND()
        LIMIT 3;
    """, (product_id,))
    alternatives = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "product": product,
        "alternatives": alternatives
    }
