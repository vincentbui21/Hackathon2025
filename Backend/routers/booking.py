from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.database import get_connection
import json



router = APIRouter(prefix="/booking", tags=["Booking"])

# Model for a single product in the order
class ProductOrder(BaseModel):
    product_id: int
    quantity: int

# Model for the full order (list of products)
class OrderRequest(BaseModel):
    items: List[ProductOrder]

@router.get("/")
async def get_products():
    # Return list of all items available
    return {"message": "All products loaded"}

@router.post("/order")
async def create_order(order_data: OrderRequest):
    # Access list of items via order_data.items
    return {"message": "Order created", "order": [item.dict() for item in order_data.items]}


@router.get("/products")
async def get_products():
    conn = get_connection()
    if conn is None:
        return {"error": "Cannot connect to database"}

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Product")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"products": products}


@router.get("/orders")
async def get_all_orders():
    """
    Fetch all orders from the database.
    Returns a list of orders with their tracking and substitution info.
    """
    conn = get_connection()
    if conn is None:
        return {"error": "Cannot connect to database"}

    cursor = conn.cursor(dictionary=True)
    query = "SELECT OrderID, Total, Status, Tracking, Substitution FROM `Order`"
    cursor.execute(query)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert JSON strings from DB to actual Python lists
    for order in orders:
        order["Tracking"] = json.loads(order["Tracking"])
        order["Substitution"] = json.loads(order["Substitution"])

    return {"orders": orders}