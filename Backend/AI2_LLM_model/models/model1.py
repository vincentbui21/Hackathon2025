import os
import json
import difflib
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI

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
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
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

    # Second turn: user asks for more
    print("\n=== Second turn (user asks for more) ===")
    print(
        model.suggest_substitutions(
            customer_message="Do you have any other alternatives?"
        )
    )

    # Third turn: user says bye
    print("\n=== Third turn (user ends) ===")
    print(
        model.suggest_substitutions(
            customer_message="Thanks, bye!"
        )
    )
