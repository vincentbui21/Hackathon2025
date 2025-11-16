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

print(get_products())
