from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

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
