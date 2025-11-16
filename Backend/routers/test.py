# from fastapi import APIRouter, UploadFile, File, Form
# from dotenv import load_dotenv
# import os
# import base64
# import json
# import requests
# from PIL import Image
# import io

# router = APIRouter(prefix="/validate", tags=["Validator"])

# load_dotenv()

# FEATHERLESS_URL = "https://api.featherless.ai/v1/chat/completions"
# API_KEY = os.getenv("FEATHERLESS_API_KEY")

# # Create folder to save uploaded images
# os.makedirs("uploaded_images", exist_ok=True)

# @router.post("/count_products")
# async def count_products(image: UploadFile = File(...), order_id: str = Form(...)):

#     # Save uploaded file
#     image_path = f"uploaded_images/{image.filename}"
#     with open(image_path, "wb") as f:
#         f.write(await image.read())

#     # Open image and resize/compress to reduce payload
#     pil_img = Image.open(image_path).convert("RGB")
#     pil_img.thumbnail((800, 800))  # resize to max 800x800
#     buffered = io.BytesIO()
#     pil_img.save(buffered, format="JPEG", quality=85)  # compress JPEG
#     img_bytes = buffered.getvalue()

#     # Encode image as base64
#     img_b64 = base64.b64encode(img_bytes).decode()

#     # Prompt for the AI
#     prompt = """
#     You are a grocery counting assistant.

#     Count how many items of each category appear in this image:
#     - chocolate
#     - cheese
#     - milk
#     - yogurt

#     Return ONLY JSON in this structure:
#     {
#         "chocolate": number,
#         "cheese": number,
#         "milk": number,
#         "yogurt": number
#     }
#     No extra text.
#     """

#     payload = {
#         "model": "google/gemma-3-27b-it",  # correct vision model
#         "messages": [
#             {"role": "user", "content": prompt},
#             {"role": "user", "content": [
#                 {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"}
#             ]}
#         ]
#     }

#     headers = {
#         "Authorization": f"Bearer {API_KEY}",
#         "Content-Type": "application/json"
#     }

#     response = requests.post(FEATHERLESS_URL, json=payload, headers=headers)

#     try:
#         ai_response = response.json()
#         raw = ai_response["choices"][0]["message"]["content"]
#         product_counts = json.loads(raw)
#     except Exception:
#         return {
#             "error": "Failed to parse AI response",
#             "raw_response": response.text
#         }

#     return {
#         "order_id": order_id,
#         "product_counts": product_counts,
#         "image_path": image_path
#     }
