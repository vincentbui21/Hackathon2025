from fastapi import APIRouter, UploadFile, File, Form

router = APIRouter(prefix="/validate", tags=["Validator"])

@router.post("/")
async def validate_order(image: UploadFile = File(...), order_id: str = Form(...)):
    # Run OpenCV and CNN detection model
    return {
        "order_id": order_id,
        "missing_items": ["milk", "potatoes"]
    }
