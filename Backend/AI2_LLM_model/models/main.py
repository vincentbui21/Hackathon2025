import time
from .model1 import ValioCustomerServiceLLM
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print("❌ Database connection failed:", e)
        return None
    
def get_products():
    conn = get_connection()
    if conn is None:
        return {"error": "Cannot connect to database"}

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Product")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"products": products}

def get_product_recommendation(product_id = None):
    all_products_dict = get_products()
    all_products = all_products_dict["products"]
    model = ValioCustomerServiceLLM()
    response = model.recommend_with_llm(product_id, all_products, amount_missing=None, customer_message=None, conversation_delete=False, order_id=None)
    return response

def talk_to_customer_service(customer_message: str = None, conversation_delete: bool = False):
    all_products_dict = get_products()
    all_products = all_products_dict["products"]
    model = ValioCustomerServiceLLM()
    response = model.recommend_with_llm(product_id=None, all_products=all_products, amount_missing=None, customer_message=customer_message, conversation_delete=False, order_id=None)
    return response

def mention_missing_products(product_id = None, amount_missing: int = None, order_id: str = None):
    all_products_dict = get_products()
    all_products = all_products_dict["products"]
    model = ValioCustomerServiceLLM()
    response = model.recommend_with_llm(product_id=product_id, all_products=all_products, amount_missing=amount_missing, customer_message=None, conversation_delete=False, order_id=order_id)
    return response

if __name__ == "__main__":
    test_product_id = 4009837852291  # Replace with a valid product ID for testing
    recommendation = get_product_recommendation(test_product_id)
    print("Recommendation Response:", recommendation)

    print("\n")

    time.sleep(2)
    
    amount_missing = 3
    product_id = 4009837852291
    order_id = "ORD123456"
    recommendation = mention_missing_products(product_id=product_id, amount_missing=amount_missing, order_id=order_id)
    print("Recommendation Response:", recommendation)

    print("\n")
    
    time.sleep(2)

    message = "Onko muita vaihtoehtoja?"
    recommendation = talk_to_customer_service(customer_message=message)
    print("Recommendation Response:", recommendation)

    print("\n")
    time.sleep(2)

    message = "bye"
    delete = True
    recommendation = talk_to_customer_service(customer_message=message, conversation_delete=delete)
    print("Recommendation Response:", recommendation)