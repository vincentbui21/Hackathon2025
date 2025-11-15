from fastapi import APIRouter, Body

router = APIRouter(prefix="/booking", tags=["Booking"])

@router.get("/")
async def get_products():
    # Return list of all items available
    return {"message": "All products loaded"}


@router.post("/order")
async def create_order(order_data: dict = Body(...)):
    # Save order to DB
    return {"message": "Order created", "order": order_data}