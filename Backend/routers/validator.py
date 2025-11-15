from fastapi import APIRouter, UploadFile, File, Form
import os
import shutil

router = APIRouter(prefix="/validate", tags=["Validator"])

UPLOAD_FOLDER = "uploads"

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@router.post("/")
async def validate_order(image: UploadFile = File(...), order_id: str = Form(...)):
    """
    Receives an image and order_id.
    Saves the file to a folder for further processing.
    """
    # Save the uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, image.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # You can also read the file content in memory
    image.file.seek(0)  # reset pointer if needed
    content = await image.read()  # bytes

    print(f"Received file: {image.filename}")
    print(f"File size: {len(content)} bytes")
    print(f"Saved at: {file_path}")

    return {
        "order_id": order_id,
        "filename": image.filename,
        "saved_path": file_path,
        "file_size": len(content)
    }
