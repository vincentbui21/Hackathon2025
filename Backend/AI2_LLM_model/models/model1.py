import os
import json
import difflib
from typing import List, Dict, Any, Optional
from langchain.chat_models import ChatOpenAI
import mysql.connector
from decimal import Decimal
import requests
import re

def safe_convert(o):
    if isinstance(o, Decimal):
        return float(o)
    return o


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

    # ---------------------------------------------------
    # 💬 ANSWER TEXT GENERATION
    # ---------------------------------------------------

    def _generate_message_for_batch(
    self,
    context: str,
    original_product: str,
    batch_names: List[str],
    is_more_batch: bool,
) -> str:
        """
        STRICT version:
        - LLM is only allowed to reference items inside batch_names.
        - Must speak in past tense.
        - Must NOT reuse old alternatives.
        - Must NOT invent new alternatives.
        - Must NOT recap previously shown items.
        """

        names_str = ", ".join(batch_names)

        if is_more_batch:
            task_text = f"""
    The customer already DID NOT receive the product "{original_product}".
    They already saw an initial list of alternative products.
    They asked specifically for MORE alternatives.

    You must produce ONE short, friendly, customer-facing sentence in PAST TENSE that:
    - apologizes again BRIEFLY for the missing item,
    - introduces ONLY these additional alternatives: {names_str},
    - does NOT repeat alternatives shown earlier,
    - does NOT mention prediction, probability, or quantity,
    - does NOT invent ANY new product names,
    - does NOT include items outside this list,
    - does NOT describe items they already saw.

    Tone examples for inspiration (do NOT copy):
    - "Sorry again that you didn’t receive {original_product}. Here are a few more alternatives you might like: …"
    - "Since {original_product} wasn’t delivered, here are some additional options that could work for you: …"

    Return ONLY the final message text. No JSON. No bullet points.
    """
        else:
            task_text = f"""
    The customer DID NOT receive the product "{original_product}" in their order.

    Write ONE short, friendly sentence in PAST TENSE that:
    - apologizes that "{original_product}" was missing,
    - introduces ONLY these suggested alternatives: {names_str},
    - does NOT mention prediction, probability, or quantity,
    - does NOT invent ANY new product names.

    Tone examples (do NOT copy):
    - "We’re sorry that {original_product} wasn’t delivered. Here are some alternatives that might work for you: …"

    Return ONLY the final message text. No JSON. No bullet points.
    """

        prompt = f"""
    You are Valio's friendly customer service assistant.

    CONTEXT (tone only):
    {context}

    TASK:
    {task_text}

    STYLE REQUIREMENTS:
    - Warm, helpful, polite.
    - PAST TENSE.
    - 1–2 sentences maximum.
    - No markdown, no lists, no JSON.
    - DO NOT invent ANY new product names.
    - DO NOT repeat older alternatives.
    - Use ONLY the products: {names_str}

    Return ONLY the final customer-facing sentence.
    """

        raw = self.llm.invoke([("human", prompt)])
        return self._strip_think(raw.content).strip()


    # ---------------------------------------------------
    # 🌟 MAIN ENTRYPOINT
    # ---------------------------------------------------

    def suggest_substitutions(
        self,
        original_product_name: Optional[str] = None,
        missing_quantity: Optional[int] = None,
        alternatives: Optional[List[Dict[str, Any]]] = None,
        customer_message: Optional[str] = None,
    ) -> str:
        """
        Main function.

        FIRST CALL (with alternatives):
        - original_product_name: name of the missing/faulty product (e.g. "Banana A")
        - missing_quantity: int, how many units are missing (e.g. 30)
        - alternatives: list of dicts, each with at least:
            {
              "product_name": str,
              "allergens": [...],
              "non_allergens": [...],
              "ingredients": [...],
              "prediction_score": float,
              "quantity": int
            }
        - customer_message: can be None on the first call

        RETURNS JSON STRING:
        {
          "Answers": "We are sorry that you did not receive Banana A ...",
          "Options": [
            {
              "product_name": "...",
              "allergens": [...],
              "non_allergens": [...],
              "ingredients": [...]
            },
            ...
          ]
        }

        FOLLOW-UP CALLS (no alternatives provided):
        - Pass only `customer_message`.
        - If the user asks for "more", returns next batch.
        - If user says "bye"/"thanks", closes nicely and can be cleaned up.
        """

        context = self._load_context()
        state = self._load_state()

        # ---------------------------------------------------
        # CASE 1: FIRST CALL WITH ALTERNATIVES
        # ---------------------------------------------------
        if alternatives is not None:
            if not original_product_name:
                original_product_name = "the original product"

            # 1) quantity filter: only products that can cover the missing_quantity
            # "super strict": if missing_quantity is provided, require quantity >= missing_quantity
            if missing_quantity is not None:
                candidates = [
                    a
                    for a in alternatives
                    if isinstance(a.get("quantity"), (int, float))
                    and a["quantity"] >= missing_quantity
                ]
            else:
                candidates = alternatives[:]

            # if nothing passes quantity filter, we don't suggest anything
            if not candidates:
                self._save_state(original_product_name, missing_quantity, [], 0)
                answers = (
                    f"We are very sorry that you did not receive {original_product_name}, "
                    "and unfortunately we do not have any suitable substitutes with enough quantity available."
                )
                result = {
                    "Answers": answers,
                    "Options": [],
                }
                # log context
                self._append_context(f"Customer said: {customer_message}")
                self._append_context(f"Model replied: {answers}")
                return json.dumps(result, ensure_ascii=False, indent=2)

            # 2) sort by prediction_score desc, then quantity desc
            candidates_sorted = sorted(
                candidates,
                key=lambda x: (-x.get("prediction_score", 0.0), -x.get("quantity", 0))
            )

            # 3) save full sorted list in state for future "more" calls
            self._save_state(
                original_product_name=original_product_name,
                missing_quantity=missing_quantity,
                sorted_alternatives=candidates_sorted,
                recommended_count=0,
            )

            # 4) pick first batch
            batch = candidates_sorted[:BATCH_SIZE]
            batch_names = [item["product_name"] for item in batch]

            # 5) generate message text (past tense)
            answers = self._generate_message_for_batch(
                context=context,
                original_product=original_product_name,
                batch_names=batch_names,
                is_more_batch=False,
            )

            # 6) update recommended count
            self._update_recommended_count(len(batch))

            # 7) log context
            self._append_context(f"Customer said: {customer_message}")
            self._append_context(f"Model replied: {answers}")

            # 8) build Options for frontend (no scores, no quantities)
            options_for_frontend = [
                {
                    "product_name": item["product_name"],
                    "allergens": item.get("allergens", []),
                    "non_allergens": item.get("non_allergens", []),
                    "ingredients": item.get("ingredients", []),
                }
                for item in batch
            ]

            result = {
                "Answers": answers,
                "Options": options_for_frontend,
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        # ---------------------------------------------------
        # CASE 2: FOLLOW-UP, STATE EXISTS (no new alternatives)
        # ---------------------------------------------------
        if state:
            original_product_name = state["original_product"]
            missing_quantity = state.get("missing_quantity")
            all_alts = state.get("sorted_alternatives", [])
            recommended_count = state.get("recommended_count", 0)

            # A) user wants to end conversation
            if user_wants_end(customer_message):
                closing = "We are glad we could assist you today. Have a great day!"
                # Optionally clear state + context here if you want:
                # self._reset_state()
                # self._reset_context()
                self._append_context(f"Customer said: {customer_message}")
                self._append_context(f"Model replied: {closing}")
                return json.dumps(
                    {"Answers": closing, "Options": []},
                    ensure_ascii=False,
                    indent=2,
                )

            # B) user explicitly wants more alternatives
            if user_wants_more(customer_message):
                next_batch = all_alts[recommended_count:recommended_count + BATCH_SIZE]

                if not next_batch:
                    # No more to show
                    answers = (
                        "We’ve already suggested all suitable alternatives that match your order, "
                        "but I’m happy to help with anything else."
                    )
                    self._append_context(f"Customer said: {customer_message}")
                    self._append_context(f"Model replied: {answers}")
                    return json.dumps(
                        {"Answers": answers, "Options": []},
                        ensure_ascii=False,
                        indent=2,
                    )

                # update count
                new_count = min(recommended_count + len(next_batch), len(all_alts))
                self._update_recommended_count(new_count)

                batch_names = [item["product_name"] for item in next_batch]

                answers = self._generate_message_for_batch(
                    context=context,
                    original_product=original_product_name,
                    batch_names=batch_names,
                    is_more_batch=True,
                )

                self._append_context(f"Customer said: {customer_message}")
                self._append_context(f"Model replied: {answers}")

                options_for_frontend = [
                    {
                        "product_name": item["product_name"],
                        "allergens": item.get("allergens", []),
                        "non_allergens": item.get("non_allergens", []),
                        "ingredients": item.get("ingredients", []),
                    }
                    for item in next_batch
                ]

                result = {
                    "Answers": answers,
                    "Options": options_for_frontend,
                }
                return json.dumps(result, ensure_ascii=False, indent=2)

            # C) normal follow-up message that is not "more" and not "bye"
            # → just a friendly reply, no Options.
            prompt = f"""
You are Valio's friendly customer service assistant.

The customer said: "{customer_message}"

Reply briefly, kindly, and professionally.
Do NOT suggest new alternatives unless the user explicitly asks for more options.

Return ONLY valid JSON:

{{
  "Answers": "string",
  "Options": []
}}
"""
            raw = self.llm.invoke([("human", prompt)])
            clean = self._strip_think(raw.content)

            self._append_context(f"Customer said: {customer_message}")
            self._append_context(f"Model replied: {clean}")

            return clean

        # ---------------------------------------------------
        # CASE 3: NO STATE, NO ALTERNATIVES → generic chat
        # ---------------------------------------------------
        prompt = f"""
You are Valio's friendly customer service assistant.

The customer said: "{customer_message}"

Reply briefly, kindly, and professionally.
Do NOT mention substitutions because we don't have product data in this call.

Return ONLY valid JSON:

{{
  "Answers": "string",
  "Options": []
}}
"""
        raw = self.llm.invoke([("human", prompt)])
        clean = self._strip_think(raw.content)
        return clean
    
        # ---------------------------------------------------
    # 🆕 PRE-PURCHASE MULTI-PRODUCT SUBSTITUTION HANDLER
    # ---------------------------------------------------
    def suggest_prepurchase_substitutions(
        self,
        risky_products: list,  
        # Example:
        # [
        #   {
        #       "product_name": "Banana A",
        #       "missing_quantity": 30,
        #       "risk_score": 0.78,
        #       "alternatives": [
        #           {"product_name": "Banana B", "allergens": [], "non_allergens": [], "ingredients": ["banana"], "prediction_score": 0.92, "quantity": 50},
        #           ...
        #       ]
        #   },
        #   {...},   # for multiple products
        # ]
        customer_message: str = None
    ):
        """
        Pre-purchase assistant.
        - Handles MULTIPLE risky products BEFORE purchase is confirmed.
        - Suggests 3 strict alternatives per product.
        - Supports follow-up questions.
        - Reuses the SAME conversation context file.
        - Uses a separate state file to manage alternative batches per product.
        """

        context = self._load_context()

        # ===============================================================
        # CASE 1 — INITIAL CALL (list of risky products is provided)
        # ===============================================================
        if risky_products:
            # Build structured state to remember alternatives for EACH risky product
            state = {
                "products": {},
                "recommended_counts": {},
            }

            response_options = {}
            response_messages = []

            for p in risky_products:
                original = p["product_name"]
                missing_qty = p["missing_quantity"]

                # Strict filtering (quantity + category)
                strict_alts = [
                    alt for alt in p["alternatives"]
                    if alt["quantity"] >= missing_qty
                ]

                # If strict filtering empties — fall back to all but still category-only.
                if not strict_alts:
                    strict_alts = p["alternatives"]

                # Sort them (prediction_score desc → quantity desc)
                sorted_alts = sorted(
                    strict_alts,
                    key=lambda x: (-x["prediction_score"], -x["quantity"])
                )

                # Save to state
                state["products"][original] = sorted_alts
                state["recommended_counts"][original] = 0

                # First 3 alternatives
                batch = sorted_alts[:3]
                batch_names = [a["product_name"] for a in batch]

                # Build user-facing message (LLM)
                msg_prompt = f"""
The customer is PRE-PURCHASE and considering buying items.

One item has low reliability:
"{original}"

Write ONE short, friendly message in PAST TENSE saying:
- "We are sorry to say that {original} may not be reliably delivered"
- "Here are some alternatives"
- Include ONLY these: {", ".join(batch_names)}
- DO NOT invent new product names.
- Tone: warm, polite, helpful.
Return ONLY the message.
"""

                raw = self.llm.invoke([("human", msg_prompt)])
                message = self._strip_think(raw.content).strip()

                # Add to response
                response_messages.append(message)
                response_options[original] = batch

                # Update counters
                state["recommended_counts"][original] = len(batch)

            # Save global state file
            with open("prepurchase_state.json", "w") as f:
                json.dump(state, f, indent=2)

            combined_message = " ".join(response_messages)

            self._append_context(f"Customer said: {customer_message}")
            self._append_context(f"Model replied: {combined_message}")

            return json.dumps(
                {
                    "Answers": combined_message,
                    "Options": response_options
                },
                ensure_ascii=False,
                indent=2
            )

        # ===============================================================
        # CASE 2 — FOLLOW-UP QUESTIONS OR NORMAL CHAT
        # ===============================================================
        if os.path.exists("prepurchase_state.json"):
            with open("prepurchase_state.json", "r") as f:
                state = json.load(f)

            products = state["products"]
            counters = state["recommended_counts"]

            # Detect which product they are asking about
            msg = (customer_message or "").lower()

            # Find product name contained in message
            target_product = None
            for product_name in products.keys():
                if product_name.lower().split()[0] in msg:
                    target_product = product_name
                    break

            # ===========================================================
            # ASK FOR MORE OPTIONS (for a specific product)
            # ===========================================================
            if target_product and user_wants_more(customer_message):
                all_alts = products[target_product]
                used = counters[target_product]

                next_batch = all_alts[used : used + 3]

                if not next_batch:
                    # No more options — polite ending
                    final_message = (
                        f"Thanks for checking! Unfortunately, we don’t have any more "
                        f"alternatives for {target_product}, but feel free to ask anything else."
                    )

                    return json.dumps(
                        {
                            "Answers": final_message,
                            "Options": {}
                        },
                        ensure_ascii=False,
                        indent=2
                    )

                # Update counter
                counters[target_product] = min(used + 3, len(all_alts))

                # Save new state
                with open("prepurchase_state.json", "w") as f:
                    json.dump(state, f, indent=2)

                batch_names = [a["product_name"] for a in next_batch]

                msg_prompt = f"""
Write ONE short, friendly sentence in past tense saying:
"Here are some more alternatives for {target_product}"
Only list: {", ".join(batch_names)}
Do not invent products.
Return ONLY the final message.
"""

                raw = self.llm.invoke([("human", msg_prompt)])
                final_msg = self._strip_think(raw.content).strip()

                return json.dumps(
                    {"Answers": final_msg, "Options": {target_product: next_batch}},
                    ensure_ascii=False,
                    indent=2
                )

            # ===========================================================
            # NORMAL CHAT (not asking for more alternatives)
            # ===========================================================
            normal_prompt = f"""
You are Valio's friendly assistant.
Customer wrote: "{customer_message}"

Reply politely in ONE sentence.
Do NOT suggest alternatives unless they explicitly ask for more.

Return ONLY:

{{
  "Answers": "string",
  "Options": {{}}
}}
"""

            raw = self.llm.invoke([("human", normal_prompt)])
            clean = self._strip_think(raw.content)

            self._append_context(f"Customer said: {customer_message}")
            self._append_context(f"Model replied: {clean}")

            return clean

        # ===============================================================
        # CASE 3 — No state, no risky products → normal chat fallback
        # ===============================================================
        return json.dumps(
            {"Answers": "How can I help you today?", "Options": {}},
            ensure_ascii=False,
            indent=2
        )
    
    def recommend_with_llm(self, product_id: str = None, all_products: list = None, customer_message: str = None):
        # Build compressed product list only if provided
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
        # MODE 1 — Recommendation mode (product_id is provided)
        # ------------------------------------------------------
        if product_id is not None:
            prompt = f"""
    You are an expert product recommendation engine.

    Your task:
    - Analyze all products below.
    - Pick the BEST 3 alternatives to product ID {product_id}.
    - Exclude the product with ID {product_id}.
    - Use your own reasoning (name similarity, price, score, etc.).
    - Output ONLY JSON.

    Products:
    {json.dumps(compressed)}

    Your response MUST be EXACTLY:

    {{
        "Answers": "Short friendly explanation.",
        "Options": [best_ID_1, best_ID_2, best_ID_3]
    }}
    """
        # ------------------------------------------------------
        # MODE 2 — Customer service mode (no product_id)
        # ------------------------------------------------------
        else:
            prompt = f"""
    You are a friendly and professional customer service agent.

    Customer message:
    "{customer_message}"

    Respond politely, briefly, warmly.

    OUTPUT RULES:
    Return ONLY valid JSON:
    {{
        "Answers": "Your friendly message here",
        "Options": []
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
                "temperature": 0.2,
                "max_tokens": 300
            }
        )

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Extract JSON (non-greedy)
        json_match = re.search(r"\{.*?\}", content, flags=re.DOTALL)
        if not json_match:
            return {"error": "No JSON detected", "raw": content}

        return json.loads(json_match.group(0))

# ---------------------------------------------------
# PRE-PURCHASE TESTS
# ---------------------------------------------------
'''
if __name__ == "__main__":
    model = ValioCustomerServiceLLM()

    risky_products = [
        {
            "product_name": "Banana A",
            "missing_quantity": 30,
            "risk_score": 0.65,
            "alternatives": [
                {"product_name": "Banana B", "allergens": [], "non_allergens": [], "ingredients": ["banana"], "prediction_score": 0.92, "quantity": 50},
                {"product_name": "Banana C", "allergens": [], "non_allergens": [], "ingredients": ["banana"], "prediction_score": 0.80, "quantity": 80},
                {"product_name": "Banana D", "allergens": [], "non_allergens": [], "ingredients": ["banana"], "prediction_score": 0.85, "quantity": 60},
                {"product_name": "Banana E", "allergens": [], "non_allergens": [], "ingredients": ["banana"], "prediction_score": 0.75, "quantity": 100},
            ]
        },
        {
            "product_name": "Apple X",
            "missing_quantity": 10,
            "risk_score": 0.71,
            "alternatives": [
                {"product_name": "Apple A", "allergens": [], "non_allergens": [], "ingredients": ["apple"], "prediction_score": 0.91, "quantity": 20},
                {"product_name": "Apple B", "allergens": [], "non_allergens": [], "ingredients": ["apple"], "prediction_score": 0.87, "quantity": 15},
                {"product_name": "Apple C", "allergens": [], "non_allergens": [], "ingredients": ["apple"], "prediction_score": 0.85, "quantity": 40},
            ]
        }
    ]

    print("=== First Turn: Initial Pre-Purchase Suggestions ===")
    print(model.suggest_prepurchase_substitutions(risky_products))

    print("=== Second Turn: Ask for more alternatives for Banana A ===")
    print(model.suggest_prepurchase_substitutions(
        risky_products=None,
        customer_message="Do you have more options for banana?"
    ))

    print("=== Third Turn: Ask for more alternatives for Apple A ===")
    print(model.suggest_prepurchase_substitutions(
        risky_products=None,
        customer_message="Do you have more options for apple?"
    ))

    print("=== Fourth Turn: Normal Chat ===")
    print(model.suggest_prepurchase_substitutions(
        risky_products=None,
        customer_message="Thanks, that's all."
    ))



# ---------------------------------------------------
# OPTIONAL LOCAL TEST
# ---------------------------------------------------
if __name__ == "__main__":
    model = ValioCustomerServiceLLM()

    # Example input from another AI / DB
    original_product_name = "Banana A"
    missing_quantity = 30

    alternatives = [
        {
            "product_name": "Banana B",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["banana"],
            "prediction_score": 0.9,
            "quantity": 100,
        },
        {
            "product_name": "Banana C",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["banana"],
            "prediction_score": 0.8,
            "quantity": 80,
        },
        {
            "product_name": "Banana D",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["banana"],
            "prediction_score": 0.85,
            "quantity": 60,
        },
        {
            "product_name": "Banana E",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["banana"],
            "prediction_score": 0.7,
            "quantity": 50,
        }
    ]

    # First turn
    print("=== First turn (system suggests alternatives) ===")
    print(
        model.suggest_substitutions(
            original_product_name=original_product_name,
            missing_quantity=missing_quantity,
            alternatives=alternatives,
            customer_message=None,
        )
    )

    # Second turn: user talks generically
    print("\n=== Second turn (user talks generically) ===")
    print(
        model.suggest_substitutions(
            customer_message="How are you"
        )
    )

    # Third turn: user asks for more
    print("\n=== Third turn (user asks for more) ===")
    print(
        model.suggest_substitutions(
            customer_message="Were there alternatives?"
        )
    )

    # Fourth turn: user asks for even more
    print("\n=== Fourth turn (user asks for even more) ===")
    print(
        model.suggest_substitutions(
            customer_message="Are there any other options?"
        )
    )

    # Fifth turn: user says thanks
    print("\n=== Fifth turn (user says thanks) ===")
    print(
        model.suggest_substitutions(
            customer_message="Thanks for your help!"
        )
    )
'''