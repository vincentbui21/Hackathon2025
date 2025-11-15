from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.database import get_connection
import json
from typing import List



router = APIRouter(prefix="/checkout", tags=["Checkout"])

class ProductIdsRequest(BaseModel):
    product_ids: List[int]

@router.post("/predict")
async def fetch_prediction_scores(request: ProductIdsRequest):
    conn = get_connection()
    if conn is None:
        return {"error": "Cannot connect to database"}

    cursor = conn.cursor(dictionary=True)

    ids_tuple = tuple(request.product_ids)
    if len(ids_tuple) == 1:
        ids_tuple = (ids_tuple[0],)

    query = f"""
        SELECT ProductID, Product_name, Prediction_score
        FROM Product
        WHERE ProductID IN {ids_tuple}
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"predictions": results}


class TrackingItem(BaseModel):
    product_id: int
    ordered_quantity: int
    real_quantity: int = 0  # initially 0 until verified

class OrderRequest(BaseModel):
    total: float
    status: str = "pending"
    tracking: List[TrackingItem]

@router.post("/order")
async def create_order(order: OrderRequest):
    conn = get_connection()
    if conn is None:
        return {"error": "Cannot connect to database"}

    cursor = conn.cursor()

    # Convert tracking list to JSON string for DB
    tracking_json = json.dumps([item.dict() for item in order.tracking])

    query = """
        INSERT INTO `Order` (Total, Status, Tracking, Substitution)
        VALUES (%s, %s, %s, %s)
    """
    values = (order.total, order.status, tracking_json, json.dumps([]))  # empty substitution

    cursor.execute(query, values)
    conn.commit()

    order_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return {"message": "Order created", "order_id": order_id}