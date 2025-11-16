import os
import json
import difflib
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
import mysql.connector
from decimal import Decimal
import requests
import re

def safe_convert(o):
    if isinstance(o, Decimal):
        return float(o)
    return o

def delete_history():
    try:
        os.remove("conversation_history.txt")
    except FileNotFoundError:
        pass

def save_to_history(role: str, message: str):
    """Append a message to the conversation history file."""
    with open("conversation_history.txt", "a") as f:
        f.write(f"{role}: {message}\n")


def load_history(max_lines: int = 20) -> str:
    """Load the most recent N lines from the history file."""
    try:
        with open("conversation_history.txt", "r") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except FileNotFoundError:
        return ""

def extract_json(content: str):
    """Extract the FIRST valid JSON object from LLM output."""

    # 1. Remove fenced ```json code blocks
    content = re.sub(r"```json(.*?)```", r"\1", content, flags=re.DOTALL)
    content = re.sub(r"```(.*?)```", r"\1", content, flags=re.DOTALL)

    # 2. Try direct load
    try:
        return json.loads(content)
    except:
        pass

    # 3. Remove comments like // text
    cleaned = re.sub(r"//.*", "", content)

    # 4. Try full cleaned content
    try:
        return json.loads(cleaned)
    except:
        pass

    # 5. Extract ANY JSON block
    blocks = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", cleaned, flags=re.DOTALL)
    for block in blocks:
        try:
            return json.loads(block)
        except:
            continue

    return None
def delete_history():
    try:
        os.remove("conversation_history.txt")
    except FileNotFoundError:
        pass

def save_to_history(role: str, message: str):
    """Append a message to the conversation history file."""
    with open("conversation_history.txt", "a") as f:
        f.write(f"{role}: {message}\n")


def load_history(max_lines: int = 20) -> str:
    """Load the most recent N lines from the history file."""
    try:
        with open("conversation_history.txt", "r") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except FileNotFoundError:
        return ""

def extract_json(content: str):
    """Extract the FIRST valid JSON object from LLM output."""

    # 1. Remove fenced ```json code blocks
    content = re.sub(r"```json(.*?)```", r"\1", content, flags=re.DOTALL)
    content = re.sub(r"```(.*?)```", r"\1", content, flags=re.DOTALL)

    # 2. Try direct load
    try:
        return json.loads(content)
    except:
        pass

    # 3. Remove comments like // text
    cleaned = re.sub(r"//.*", "", content)

    # 4. Try full cleaned content
    try:
        return json.loads(cleaned)
    except:
        pass

    # 5. Extract ANY JSON block
    blocks = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", cleaned, flags=re.DOTALL)
    for block in blocks:
        try:
            return json.loads(block)
        except:
            continue

    return None

CONTEXT_FILE = "customer_context.txt"
ALT_MEMORY_FILE = "alternatives_memory.json"
BATCH_SIZE = 3  # number of alternatives shown at a time


# ---------------------------------------------------
# 🔍 FUZZY MATCHING HELPERS
# ---------------------------------------------------

REQUEST_MORE_KEYWORDS = [
    "more",
    "other",
    "next",
    "else",
    "anything else",
    "any other",
    "more options",
    "more alternatives",
    "recommend more",
    "show more",
    "more choices",
    "another option",
]

END_KEYWORDS = [
    "bye",
    "goodbye",
    "thanks",
    "thank you",
    "kiitos",
    "that’s all",
    "thats all",
    "that's it",
    "thats it",
    "all good",
    "ok good",
    "we're done",
    "were done",
]

def fetch_product_and_generate_alternatives(product_id: int):
    """
    Fetch the target product and automatically generate alternative products
    by scanning the database for matching allergens / non-allergens.

    RETURNS:
    {
        "original_product_name": str,
        "missing_quantity": int or None,
        "alternatives": [
            {
                "product_name": str,
                "allergens": [...],
                "non_allergens": [...],
                "ingredients": [...],
                "prediction_score": float,
                "quantity": int
            },
            ...
        ]
    }
    """

    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
    )
    cursor = conn.cursor(dictionary=True)

    # ----------------------------------------------------------
    # 1. Fetch original product
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT 
            ProductID,
            Product_name,
            Allergens,
            Non_allergens,
            Quantity,
            Prediction_score,
            Ingredients
        FROM Product
        WHERE ProductID = %s
    """, (product_id,))

    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Product ID {product_id} does not exist in DB")

    original_name   = row["Product_name"]
    original_algs   = row["Allergens"] or []
    original_nonalg = row["Non_allergens"] or []
    original_ing    = row["Ingredients"] or []

    # Convert DB JSON/text fields -> Python lists
    if isinstance(original_algs, str):
        original_algs = json.loads(original_algs)
    if isinstance(original_nonalg, str):
        original_nonalg = json.loads(original_nonalg)
    if isinstance(original_ing, str):
        original_ing = json.loads(original_ing)

    # ----------------------------------------------------------
    # 2. Fetch ALL other products in DB to compare against
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT 
            ProductID,
            Product_name,
            Allergens,
            Non_allergens,
            Ingredients,
            Prediction_score,
            Quantity
        FROM Product
        WHERE ProductID != %s
    """, (product_id,))
    
    all_products = cursor.fetchall()
    conn.close()

    alternatives = []

    # ----------------------------------------------------------
    # 3. Strict filtering: match allergens / non-allergens
    # ----------------------------------------------------------
    def is_strict_match(prod):
        # Convert fields
        pa = prod["Allergens"] or []
        pna = prod["Non_allergens"] or []
        ing = prod["Ingredients"] or []

        if isinstance(pa, str): pa = json.loads(pa)
        if isinstance(pna, str): pna = json.loads(pna)
        if isinstance(ing, str): ing = json.loads(ing)

        # STRICT RULES:
        # 1. No allergen conflicts
        if any(a in original_algs for a in pa):
            return False

        # 2. Must share non-allergens or ingredients meaningfully
        shared = len(set(pna) & set(original_nonalg)) + len(set(ing) & set(original_ing))
        return shared > 0

    for prod in all_products:
        if is_strict_match(prod):
            alternatives.append({
                "product_name": prod["Product_name"],
                "allergens": json.loads(prod["Allergens"]) if isinstance(prod["Allergens"], str) else prod["Allergens"],
                "non_allergens": json.loads(prod["Non_allergens"]) if isinstance(prod["Non_allergens"], str) else prod["Non_allergens"],
                "ingredients": json.loads(prod["Ingredients"]) if isinstance(prod["Ingredients"], str) else prod["Ingredients"],
                "prediction_score": prod["Prediction_score"],
                "quantity": prod["Quantity"]
            })

    # ----------------------------------------------------------
    # 4. Sort by (prediction DESC → quantity DESC)
    # ----------------------------------------------------------
    alternatives = sorted(
        alternatives,
        key=lambda x: (-x["prediction_score"], -x["quantity"])
    )

    return {
        "original_product_name": original_name,
        "original_allergens": original_algs,
        "original_non_allergens": original_nonalg,
        "original_ingredients": original_ing,
        "alternatives": alternatives
    }


def _normalize(message: Optional[str]) -> str:
    return (message or "").lower().strip()


def user_wants_more(message: Optional[str]) -> bool:
    """Detect if customer explicitly wants more alternatives."""
    if not message:
        return False

    msg = _normalize(message)

    # direct substring match
    for kw in REQUEST_MORE_KEYWORDS:
        if kw in msg:
            return True

    # fuzzy word-level match
    for word in msg.split():
        if difflib.get_close_matches(word, REQUEST_MORE_KEYWORDS, cutoff=0.65):
            return True

    return False


def user_wants_end(message: Optional[str]) -> bool:
    """Detect if the customer is saying goodbye / ending the conversation."""
    if not message:
        return False

    msg = _normalize(message)

    for kw in END_KEYWORDS:
        if kw in msg:
            return True

    return False


# ---------------------------------------------------
# ⚙️ LLM CLASS
# ---------------------------------------------------

class ValioCustomerServiceLLM:
    """
    Core LLM wrapper for Valio chatbot.

    High-level behavior:
    - First call: given original product + missing quantity + alternatives from DB,
      filter & sort in Python, pick top 3, and ask the LLM to generate a friendly
      apology/answer in past tense.
      Returns:
      {
        "Answers": "...",
        "Options": [
          {
            "product_name": str,
            "allergens": [...],
            "non_allergens": [...],
            "ingredients": [...]
          },
          ...
        ]
      }

    - Follow-up calls: if user asks for "more", return the next batch of 3
      from the same sorted list until exhausted.

    - Conversation lines are appended to customer_context.txt.
    - Internal alternative state stored in alternatives_memory.json.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=os.getenv("FEATHERLESS_API_KEY"),
            base_url="https://api.featherless.ai/v1",
            model="deepseek-ai/DeepSeek-R1-0528",
            timeout=15,
        )

    # ---------------------------------------------------
    # 🧠 CONTEXT MEMORY
    # ---------------------------------------------------

    def _load_context(self) -> str:
        if not os.path.exists(CONTEXT_FILE):
            return ""
        with open(CONTEXT_FILE, "r") as f:
            return f.read()

    def _append_context(self, text: str) -> None:
        with open(CONTEXT_FILE, "a") as f:
            f.write(text + "\n")

    def _reset_context(self) -> None:
        if os.path.exists(CONTEXT_FILE):
            os.remove(CONTEXT_FILE)

    # ---------------------------------------------------
    # 💾 ALTERNATIVE STATE MEMORY
    # ---------------------------------------------------

    def _save_state(
        self,
        original_product_name: str,
        missing_quantity: Optional[int],
        sorted_alternatives: List[Dict[str, Any]],
        recommended_count: int = 0,
    ) -> None:
        data = {
            "original_product": original_product_name,
            "missing_quantity": missing_quantity,
            "sorted_alternatives": sorted_alternatives,
            "recommended_count": recommended_count,
        }
        with open(ALT_MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _load_state(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(ALT_MEMORY_FILE):
            return None
        with open(ALT_MEMORY_FILE, "r") as f:
            return json.load(f)

    def _update_recommended_count(self, new_count: int) -> None:
        state = self._load_state()
        if not state:
            return
        state["recommended_count"] = new_count
        with open(ALT_MEMORY_FILE, "w") as f:
            json.dump(state, f, indent=2)

    def _reset_state(self) -> None:
        if os.path.exists(ALT_MEMORY_FILE):
            os.remove(ALT_MEMORY_FILE)

    # ---------------------------------------------------
    def _strip_think(self, text: str) -> str:
        if "<think>" in text and "</think>" in text:
            return text.split("</think>")[-1].strip()
        return text.strip()

    def recommend_with_llm(
            self, 
            product_id: str = None, 
            all_products: list = None, 
            amount_missing: int = None,
            customer_message: str = None,
            conversation_delete: bool = False
        ):

        # Build compressed product list
        compressed = None
        if all_products:
            compressed = [
                {
                    "id": int(p["ProductID"]),
                    "name": p["Product_name"],
                    "price": float(p["Price"]),
                    "score": float(p["Prediction_score"])
                }
                for p in all_products
            ]

        API_KEY = os.getenv("FEATHERLESS_API_KEY")
        if not API_KEY:
            raise ValueError("Missing FEATHERLESS_API_KEY")

        API_URL = "https://api.featherless.ai/v1/chat/completions"
        MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"

        # ------------------------------------------------------
        # MODE 2 — Missing Item (special case)
        # ------------------------------------------------------
        if product_id is not None and amount_missing is not None:
            prompt = f"""
        You are an apologetic customer service agent AND a recommendation engine.

        A customer reports that {amount_missing} units of product ID {product_id}
        are missing from their delivery.

        Your goals:
        1. Apologize politely.
        2. Offer compensation (free next-day shipping, refund, or replacement).
        3. Recommend 3 product alternatives based on score, availability, and similarity.
        4. Output ONLY valid JSON.

        Products:
        {json.dumps(compressed)}

        YOUR OUTPUT (IMPORTANT):

        {{
            "Answers": "Apology + compensation + short friendly message.",
            "Options": [best_ID_1, best_ID_2, best_ID_3]
        }}
        """

        # ------------------------------------------------------
        # MODE 1 — Normal Recommendation mode
        # ------------------------------------------------------
        elif product_id is not None:
        elif product_id is not None:
            prompt = f"""
        You are an expert product recommendation engine.
        You are an expert product recommendation engine.

        Your task:
        - Pick the BEST 3 alternatives to product ID {product_id}.
        - Exclude the product with ID {product_id}.
        - Output ONLY JSON.
        Your task:
        - Pick the BEST 3 alternatives to product ID {product_id}.
        - Exclude the product with ID {product_id}.
        - Output ONLY JSON.

        Products:
        {json.dumps(compressed)}
        Products:
        {json.dumps(compressed)}

        {{
            "Answers": "Short friendly explanation.",
            "Options": [best_ID_1, best_ID_2, best_ID_3]
        }}
        """

        {{
            "Answers": "Short friendly explanation.",
            "Options": [best_ID_1, best_ID_2, best_ID_3]
        }}
        """

        # ------------------------------------------------------
        # MODE 3 — Conversation mode
        # MODE 3 — Conversation mode
        # ------------------------------------------------------
        else:
            history = load_history()
            history = load_history()
            prompt = f"""
        You are a friendly and professional customer service agent.

        Conversation history:
        {history}
        You are a friendly and professional customer service agent.

        Conversation history:
        {history}

        Customer message:
        "{customer_message}"
        Customer message:
        "{customer_message}"

        OUTPUT ONLY JSON IF CUSTOMER IS ASKING FOR MORE ALTERNATIVES:
        {{
            "Answers": "Your friendly message.",
            "Options": [best_ID_1, best_ID_2, best_ID_3]
        }}

        IF CUSTOMER IS JUST CHATTING, RESPOND:
        {{
            "Answers": "Your friendly message."
        }}
        """
        OUTPUT ONLY JSON IF CUSTOMER IS ASKING FOR MORE ALTERNATIVES:
        {{
            "Answers": "Your friendly message.",
            "Options": [best_ID_1, best_ID_2, best_ID_3]
        }}

        IF CUSTOMER IS JUST CHATTING, RESPOND:
        {{
            "Answers": "Your friendly message."
        }}
        """

        # Call API
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 300
            }
        )

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Extract JSON with robust extractor
        result = extract_json(content)
        if result is None:
            return {"error": "No valid JSON found", "raw": content}

        # Save history
        if customer_message:
            save_to_history("User", customer_message)
        if "Answers" in result:
            save_to_history("AI", result["Answers"])
        if product_id is not None and "Options" in result:
            save_to_history("AI", f"Recommended product IDs: {result['Options']}")
        
        if conversation_delete:
            delete_history()

        return result

        # Extract JSON with robust extractor
        result = extract_json(content)
        if result is None:
            return {"error": "No valid JSON found", "raw": content}

        # Save history
        if customer_message:
            save_to_history("User", customer_message)
        if "Answers" in result:
            save_to_history("AI", result["Answers"])
        if product_id is not None and "Options" in result:
            save_to_history("AI", f"Recommended product IDs: {result['Options']}")
        
        if conversation_delete:
            delete_history()

        return result
