from fastapi import APIRouter, UploadFile, File, Form
import os
import shutil
import json
from app.database import get_connection
from groq import Groq
from dotenv import load_dotenv
import base64

load_dotenv()

print("🔑 GROQ API Key Loaded:", os.getenv("GROQ_API_KEY") is not None)
print(os.getenv("GROQ_API_KEY"))

router = APIRouter(prefix="/validate", tags=["Validator"])

UPLOAD_FOLDER = "uploads"

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_products_in_order(order_id: int):
    """
    Retrieves all products in an order by order_id.

    Args:
        order_id: The ID of the order

    Returns:
        List of dictionaries with 'name' and 'quantity' for all products in the order.
        Returns empty list if order not found or on error.
    """
    conn = get_connection()
    if conn is None:
        print("❌ Cannot connect to database")
        return []

    try:
        cursor = conn.cursor(dictionary=True)

        # Get the order with its tracking data
        query = "SELECT Tracking FROM `Order` WHERE OrderID = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()

        if not result:
            print(f"⚠️ Order {order_id} not found")
            return []

        # Parse the tracking JSON
        tracking_data = json.loads(result['Tracking'])

        # Extract product IDs from tracking
        product_ids = [item['product_id'] for item in tracking_data]

        if not product_ids:
            return []

        # Fetch complete product details using JOIN
        print(f"🔍 Looking up product IDs: {product_ids}")

        # Create placeholders for parameterized query
        placeholders = ', '.join(['%s'] * len(product_ids))
        product_query = f"""
            SELECT *
            FROM Product
            WHERE ProductID IN ({placeholders})
        """
        cursor.execute(product_query, product_ids)
        products = cursor.fetchall()

        print(f"📦 Found {len(products)} products in database")

        # Create a mapping of product_id to full product data
        product_map = {p['ProductID']: p for p in products}

        # Extract product names with quantities
        result_list = []
        for item in tracking_data:
            product_id = item['product_id']
            product_data = product_map.get(product_id)

            if product_data:
                result_list.append({
                    'name': product_data['Product_name'],
                    'quantity': item['ordered_quantity']
                })
            else:
                result_list.append({
                    'name': 'Unknown',
                    'quantity': item['ordered_quantity']
                })

        cursor.close()
        return result_list

    except Exception as e:
        print(f"❌ Error fetching products for order {order_id}: {e}")
        return []
    finally:
        conn.close()

def validate_image_with_groq(image_path: str, expected_products: list) -> bool:
    """
    Uses Groq's Llama 4 Scout model to validate if products and quantities in the image
    match the expected products list.

    Args:
        image_path: Path to the saved image file
        expected_products: List of dicts with 'name' and 'quantity' keys

    Returns:
        True if image contents match expected products, False otherwise
    """
    try:
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Format expected products for the prompt
        products_text = "\n".join([f"- {p['name']}: {p['quantity']} unit(s)" for p in expected_products])

        print(products_text)

        # Create Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Create the prompt
        prompt = f"""You are a product validation assistant. Analyze the image and determine if the products and their quantities visible in the image match the expected order.

Expected products in the order:
{products_text}

Instructions:
1. Carefully examine the image to identify all visible products
2. Count the quantity of each product type
3. Compare the products and quantities you see with the expected list above
4. Respond with ONLY "true" if ALL products and quantities match exactly
5. Respond with ONLY "false" if there are any mismatches, missing items, or extra items

Your response (true or false):"""

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_completion_tokens=10,
            top_p=1,
            stream=False
        )

        # Get the response
        response = completion.choices[0].message.content.strip().lower()
        print(f"Groq validation response: {response}")

        return response == "true"

    except Exception as e:
        print(f"❌ Error validating image with Groq: {e}")
        return False

def update_order_status(order_id: int, status: str) -> bool:
    """
    Updates the status of an order.

    Args:
        order_id: The ID of the order
        status: The new status (e.g., "completed", "pending", "failed")

    Returns:
        True if update successful, False otherwise
    """
    conn = get_connection()
    if conn is None:
        print("❌ Cannot connect to database")
        return False

    try:
        cursor = conn.cursor()

        query = "UPDATE `Order` SET Status = %s WHERE OrderID = %s"
        cursor.execute(query, (status, order_id))
        conn.commit()

        cursor.close()
        print(f"✅ Order {order_id} status updated to: {status}")
        return True

    except Exception as e:
        print(f"❌ Error updating order status: {e}")
        return False
    finally:
        conn.close()

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

    # Retrieve products from order_id
    products_in_order = get_products_in_order(int(order_id))

    print(f"Products in order {order_id}: {products_in_order}")

    # Validate the image against expected products
    is_valid = validate_image_with_groq(file_path, products_in_order)

    if is_valid:
        # Update order status to completed
        update_order_status(int(order_id), "completed")
        validation_result = "Order validated successfully! Status updated to completed."
        error_type = None
    else:
        # print("Hello World")
        validation_result = "AI counting failed. Products/quantities in image do not match the order."
        error_type = "ai_counting_failed"

    return {
        "order_id": order_id,
        "filename": image.filename,
        "saved_path": file_path,
        "file_size": len(content),
        "products_in_order": products_in_order,
        "validation_passed": is_valid,
        "message": validation_result,
        "error_type": error_type
    }
