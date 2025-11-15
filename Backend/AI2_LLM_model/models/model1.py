import os
import json
import difflib
import time
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI

CONTEXT_FILE = "customer_context.txt"
ALT_MEMORY_FILE = "alternatives_memory.json"
BATCH_SIZE = 3  # number of alternatives revealed at a time

# ---------------------------------------------------
# 🔍 FUZZY MATCHING: detect “more alternatives”
# ---------------------------------------------------
REQUEST_MORE_KEYWORDS = [
    "more",
    "other",
    "next",
    "else",
    "anything",
    "any other",
    "more options",
    "more alternatives",
    "recommend more",
    "show more",
    "more choices",
    "another option",
    "another one",
]


def user_wants_more(message: Optional[str]) -> bool:
    """Detect if customer explicitly wants more alternatives."""
    if not message:
        return False

    msg = message.lower().strip()

    # direct keyword match
    for kw in REQUEST_MORE_KEYWORDS:
        if kw in msg:
            return True

    # fuzzy matching for typos / weird phrasing
    for word in msg.split():
        if difflib.get_close_matches(word, REQUEST_MORE_KEYWORDS, cutoff=0.65):
            return True

    return False


# ---------------------------------------------------
# ⚙️ LLM CLASS
# ---------------------------------------------------
class ValioCustomerServiceLLM:
    """
    Core LLM wrapper for Valio substitutions.

    ✅ Super strict:
       - Python decides which alternatives are valid
       - LLM **never** invents products
       - LLM **only** generates the human-friendly `Answers` text

    Expected alternative structure from DB:
    {
        "product_name": "Banana B",
        "allergens": ["AU", "IU"],
        "non_allergens": ["BK", "AT"],
        "ingredients": ["banana"],
        "prediction_score": 0.91,
        ...
    }
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

    # ---------------------------------------------------
    # 💾 ALTERNATIVE MEMORY (for follow-up batches)
    # ---------------------------------------------------
    def _save_state(self, original_product: str, alternatives: List[Dict[str, Any]]) -> None:
        data = {
            "original_product": original_product,
            "sorted_alternatives": alternatives,
            "recommended_count": 0,
        }
        with open(ALT_MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _load_state(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(ALT_MEMORY_FILE):
            return None
        with open(ALT_MEMORY_FILE, "r") as f:
            return json.load(f)

    def _update_recommended_count(self, count: int) -> None:
        data = self._load_state()
        if not data:
            return
        data["recommended_count"] = count
        with open(ALT_MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def reset_conversation(self) -> None:
        """Call this when the customer presses 'end conversation'."""
        if os.path.exists(CONTEXT_FILE):
            os.remove(CONTEXT_FILE)
        if os.path.exists(ALT_MEMORY_FILE):
            os.remove(ALT_MEMORY_FILE)

    # ---------------------------------------------------
    def _strip_think(self, text: str) -> str:
        if "<think>" in text and "</think>" in text:
            return text.split("</think>")[-1].strip()
        return text.strip()

    # ---------------------------------------------------
    # 🧪 SUPER-STRICT FILTERING
    # ---------------------------------------------------
    def _main_token_from_name(self, name: str) -> str:
        """
        Super simple heuristic: first word of product name.
        e.g. "Banana A" -> "banana"
        """
        if not name:
            return ""
        return name.strip().split()[0].lower()

    def _filter_strict(
        self,
        original_product: str,
        alternatives: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Super strict filtering:
        - Only keep alternatives that look like the same product type.
        - Based on name token & ingredients overlap.

        This guarantees:
        - If original is Banana A → you only get Banana B/C/D/E, never Apple or Orange.
        """

        main_token = self._main_token_from_name(original_product)

        strict_alts: List[Dict[str, Any]] = []
        for alt in alternatives:
            alt_name = alt.get("product_name", "")
            alt_token = self._main_token_from_name(alt_name)

            ingredients = alt.get("ingredients") or []
            ingredients_lower = [ing.lower() for ing in ingredients]

            # Condition 1: same main word (Banana A -> Banana B)
            same_token = (alt_token == main_token) if main_token else False

            # Condition 2: ingredient-based: original token appears as ingredient
            token_in_ingredients = main_token in ingredients_lower if main_token else False

            if same_token or token_in_ingredients:
                strict_alts.append(alt)

        # If everything gets filtered out, we keep all → but you said "super strict",
        # so here we **do not** bring back apples/oranges. We just accept fewer options.
        return strict_alts

    # ---------------------------------------------------
    # 💬 MESSAGE GENERATION FOR BATCHES
    # ---------------------------------------------------
    def _generate_message_for_batch(
        self,
        context: str,
        original_product: str,
        batch: List[Dict[str, Any]],
        prediction_value: Optional[float],
        customer_message: Optional[str],
        is_more_batch: bool,
    ) -> str:
        names = ", ".join(item["product_name"] for item in batch)

        if is_more_batch:
            task_text = f"""
The customer already saw some alternatives and asked for more
(latest message: "{customer_message}").

Write ONE short, friendly sentence introducing these additional alternatives:
{names}.
"""
        else:
            if prediction_value is not None:
                task_text = f"""
The requested product "{original_product}" may not be reliably deliverable
(prediction: {prediction_value}).

Write ONE short, friendly sentence explaining this gently and recommending these alternatives:
{names}.
"""
            else:
                task_text = f"""
The requested product "{original_product}" may not be deliverable.

Write ONE short, friendly sentence explaining this gently and recommending these alternatives:
{names}.
"""

        prompt = f"""
You are Valio's friendly customer service assistant.
Use the context below to keep tone consistent.

CONTEXT:
{context}

TASK:
{task_text}

STYLE:
- Warm, polite, and natural.
- 1–2 sentences maximum.
- No markdown, no bullet points, no JSON.
- Do NOT mention scores, probabilities, or internal logic.
- Just speak like a helpful human.

Return only the final message text.
"""

        raw = self.llm.invoke([("human", prompt)])
        msg = self._strip_think(raw.content).strip()
        return msg

    # ---------------------------------------------------
    # 🌟 MAIN ENTRYPOINT
    # ---------------------------------------------------
    def suggest_substitutions(
        self,
        original_product: Optional[str] = None,
        prediction_value: Optional[float] = None,
        alternatives: Optional[List[Dict[str, Any]]] = None,
        customer_message: Optional[str] = None,
    ) -> str:
        """
        Main function:

        - First call (with alternatives):
            * Filter strictly by type (banana → only bananas)
            * Sort by prediction_score & availability if present
            * Store state
            * Return first batch + nice answer

        - Follow-up call (no alternatives, just customer_message):
            * If user asks for more → return next batch
            * Else → normal small chat reply with no options

        Return JSON (string) in this format:

        {
            "Answers": "We are really sorry that .....",
            "Options": [
                {
                    "product_name": "chocolate cake",
                    "allergens": [...],
                    "non_allergens": [...],
                    "ingredients": [...]
                },
                ...
            ]
        }
        """

        context = self._load_context()

        # ---------------------------------------------------
        # CASE 1 — FIRST CALL (alternatives provided)
        # ---------------------------------------------------
        if alternatives:
            if not original_product:
                original_product = "this product"

            # 1) Super-strict filter
            strict_alts = self._filter_strict(original_product, alternatives)

            if not strict_alts:
                # No good same-type substitutes found
                result = {
                    "Answers": (
                        f"We are really sorry, but we couldn't find any close substitutes for {original_product}."
                        " I'm happy to help with anything else you might need."
                    ),
                    "Options": [],
                }
                return json.dumps(result, ensure_ascii=False, indent=2)

            # 2) Sort by prediction_score (if present), then maybe availability
            def sort_key(a: Dict[str, Any]):
                score = a.get("prediction_score", 0.0)
                availability = a.get("availability", 0)
                return (-score, -availability)

            alternatives_sorted = sorted(strict_alts, key=sort_key)

            # 3) Save state for follow-ups
            self._save_state(original_product, alternatives_sorted)

            # 4) First batch
            batch = alternatives_sorted[:BATCH_SIZE]

            final_message = self._generate_message_for_batch(
                context=context,
                original_product=original_product,
                batch=batch,
                prediction_value=prediction_value,
                customer_message=customer_message,
                is_more_batch=False,
            )

            # update counter
            self._update_recommended_count(len(batch))

            # log context
            self._append_context(f"Customer said: {customer_message}")
            self._append_context(f"Model replied: {final_message}")

            # Shape options to required schema (drop internal fields if you want)
            options_payload = [
                {
                    "product_name": item.get("product_name"),
                    "allergens": item.get("allergens", []),
                    "non_allergens": item.get("non_allergens", []),
                    "ingredients": item.get("ingredients", []),
                }
                for item in batch
            ]

            result = {
                "Answers": final_message,
                "Options": options_payload,
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        # ---------------------------------------------------
        # CASE 2 — FOLLOW-UP (state exists)
        # ---------------------------------------------------
        state = self._load_state()

        if state:
            all_alts = state["sorted_alternatives"]
            count = state["recommended_count"]
            original_product_saved = state["original_product"]

            if user_wants_more(customer_message):
                # next batch
                next_batch = all_alts[count:count + BATCH_SIZE]

                if not next_batch:
                    result = {
                        "Answers": (
                            "Thanks for checking! There aren’t any more close alternatives to show right now, "
                            "but I’m happy to help with anything else."
                        ),
                        "Options": [],
                    }
                    return json.dumps(result, ensure_ascii=False, indent=2)

                new_count = min(count + BATCH_SIZE, len(all_alts))
                self._update_recommended_count(new_count)

                final_message = self._generate_message_for_batch(
                    context=context,
                    original_product=original_product_saved,
                    batch=next_batch,
                    prediction_value=None,
                    customer_message=customer_message,
                    is_more_batch=True,
                )

                self._append_context(f"Customer said: {customer_message}")
                self._append_context(f"Model replied: {final_message}")

                options_payload = [
                    {
                        "product_name": item.get("product_name"),
                        "allergens": item.get("allergens", []),
                        "non_allergens": item.get("non_allergens", []),
                        "ingredients": item.get("ingredients", []),
                    }
                    for item in next_batch
                ]

                result = {
                    "Answers": final_message,
                    "Options": options_payload,
                }
                return json.dumps(result, ensure_ascii=False, indent=2)

            # Not asking for more → normal response, no options
            prompt = f"""
You are Valio's friendly customer service assistant.

A customer wrote: "{customer_message}"

Reply briefly and kindly.
Do NOT mention product options or substitutions.

Return ONLY JSON:

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
        # CASE 3 — No alternatives, no state → pure chat
        # ---------------------------------------------------
        prompt = f"""
You are Valio's friendly customer service assistant.

The customer said: "{customer_message}"

Reply briefly, kindly, and professionally.

Return ONLY JSON:

{{
  "Answers": "string",
  "Options": []
}}
"""
        raw = self.llm.invoke([("human", prompt)])
        clean = self._strip_think(raw.content)
        return clean


# ---------------------------------------------------
# OPTIONAL TEST
# ---------------------------------------------------
if __name__ == "__main__":
    model = ValioCustomerServiceLLM()

    original_product = "Banana A"

    initial_alternatives = [
        {
            "product_name": "Banana B",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["banana"],
            "prediction_score": 0.9,
            "availability": 100,
        },
        {
            "product_name": "Banana C",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["banana"],
            "prediction_score": 0.8,
            "availability": 80,
        },
        {
            "product_name": "Banana D",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["banana"],
            "prediction_score": 0.85,
            "availability": 60,
        },
        {
            "product_name": "Banana E",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["banana"],
            "prediction_score": 0.7,
            "availability": 50,
        },
        {
            "product_name": "Apple A",
            "allergens": [],
            "non_allergens": [],
            "ingredients": ["apple"],
            "prediction_score": 0.95,
            "availability": 200,
        },
    ]

    print("=== First turn (system suggests alternatives) ===")
    start_time = time.time()
    print(
        model.suggest_substitutions(
            original_product=original_product,
            prediction_value=0.7,
            alternatives=initial_alternatives,
            customer_message=None,
        )
    )
    end_time = time.time()
    print(f"First call took {end_time - start_time:.2f} seconds")

    print("\n=== Second turn (user asks for more) ===")
    start_time = time.time()
    print(
        model.suggest_substitutions(
            customer_message="Do you have any other alternatives?"
        )
    )
    end_time = time.time()
    print(f"Second call took {end_time - start_time:.2f} seconds")
