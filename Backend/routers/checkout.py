from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/checkout", tags=["Checkout"])

# Request model: list of product IDs
class PredictRequest(BaseModel):
    product_ids: List[int]

# Response model: prediction per product
class Prediction(BaseModel):
    product_id: int
    score: float  # AI prediction score (0-1, for example)

class PredictResponse(BaseModel):
    predictions: List[Prediction]

@router.post("/predict", response_model=PredictResponse)
async def predict_order_issues(request: PredictRequest):
    predictions = []
    for pid in request.product_ids:
        # Here you would call AI Agent 1 to get the actual prediction
        score = 0.5  # Placeholder, replace with AI result
        predictions.append({"product_id": pid, "score": score})

    return {"predictions": predictions}


