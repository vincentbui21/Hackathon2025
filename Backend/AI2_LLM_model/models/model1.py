import os
import json
import difflib
import time
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
]


def user_wants_more(message: str) -> bool:
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
    def _save_state(self, original_product: str, alternatives: list) -> None:
        data = {
            "original_product": original_product,
            "sorted_alternatives": alternatives,
            "recommended_count": 0,
        }
        with open(ALT_MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _load_state(self):
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

    # ---------------------------------------------------
    def _strip_think(self, text: str) -> str:
        if "<think>" in text and "</think>" in text:
            return text.split("</think>")[-1].strip()
        return text.strip()

    # ---------------------------------------------------
    # 🧪 RELEVANCE FILTERING
    # ---------------------------------------------------
    def _filter_relevant(self, original_product: str, alternatives: list) -> list:
        """
        Use LLM to classify each alternative as relevant / not_relevant
        relative to the original product. Returns only relevant ones.
        """

        if not original_product:
            # If somehow missing, skip filtering
            return alternatives

        alt_names = "\n".join([f"- {a['name']}" for a in alternatives])

        prompt = f"""
You are a product-substitution classifier.

The customer originally requested:
"{original_product}"

Below is a list of possible alternatives:
{alt_names}

TASK:
For EACH listed product, decide if it is a suitable substitute for the original product.

RULES:
- "relevant" → same general product category or usage (e.g. milk ↔ oat milk / lactose-free milk / yogurt drink).
- "not_relevant" → different category (e.g. milk ↔ banana, apple, bread).
- Focus on realistic grocery substitution, not just allergens.

OUTPUT:
Return ONLY valid JSON in this format:

{{
  "classification": [
    {{"name": "string", "label": "relevant" | "not_relevant"}}
  ]
}}
"""

        raw = self.llm.invoke([("human", prompt)])
        clean = self._strip_think(raw.content)

        try:
            parsed = json.loads(clean)
            classification = parsed.get("classification", [])
        except Exception:
            # If classification fails, be safe and keep all alternatives
            return alternatives

        relevant_names = {
            c["name"]
            for c in classification
            if c.get("label") == "relevant"
        }

        filtered = [a for a in alternatives if a["name"] in relevant_names]

        # If everything gets filtered out, fall back to original list
        return filtered if filtered else alternatives

    # ---------------------------------------------------
    # 💬 MESSAGE GENERATION FOR BATCHES
    # ---------------------------------------------------
    def _generate_message_for_batch(
        self,
        context: str,
        original_product: str,
        batch: list,
        prediction_value: float | None,
        customer_message: str | None,
        is_more_batch: bool,
    ) -> str:
        names = ", ".join(item["name"] for item in batch)

        if is_more_batch:
            task_text = f"""
The customer already saw some alternatives and asked for more
(latest message: "{customer_message}").

Write ONE short, friendly sentence introducing these additional alternatives:
{names}.
"""
        else:
            task_text = f"""
The requested product "{original_product}" may not be reliably deliverable
(prediction: {prediction_value}).

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
        original_product: str = None,
        prediction_value: float = None,
        alternatives: list | None = None,
        customer_message: str | None = None,
    ) -> str:
        """
        Main function:
        - If alternatives are provided → classify relevance, sort, store, return first batch.
        - If no alternatives but state exists → handle follow-ups or normal messages.
        - If no state → normal customer-service reply.
        """

        context = self._load_context()

        # ---------------------------------------------------
        # CASE 1 — FIRST CALL (alternatives provided)
        # ---------------------------------------------------
        if alternatives:
            # Step 1: filter out irrelevant alternatives (e.g., bananas for milk)
            relevant_alts = self._filter_relevant(original_product, alternatives)

            if not relevant_alts:
                result = {
                    "final_message": (
                        "Thanks for your interest! Right now we don't have good substitute products "
                        "for that specific item, but I’m happy to help with anything else."
                    ),
                    "chosen_alternatives": [],
                }
                return json.dumps(result, ensure_ascii=False, indent=2)

            # Step 2: sort relevant alternatives by predicted_success, then availability
            alternatives_sorted = sorted(
                relevant_alts,
                key=lambda x: (-x["predicted_success"], -x["availability"])
            )

            # Save state for later follow-ups
            self._save_state(original_product, alternatives_sorted)

            # First batch
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

            result = {
                "final_message": final_message,
                "chosen_alternatives": batch,
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
                        "final_message": (
                            "Thanks for checking! There aren’t any more alternatives left to show, "
                            "but I’m happy to help with anything else."
                        ),
                        "chosen_alternatives": [],
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

                result = {
                    "final_message": final_message,
                    "chosen_alternatives": next_batch,
                }
                return json.dumps(result, ensure_ascii=False, indent=2)

            # Not asking for more → normal response, no alternatives
            prompt = f"""
You are Valio's friendly customer service assistant.

A customer wrote: "{customer_message}"

Reply briefly and kindly.
Do NOT mention alternatives unless they ask for more.

Return ONLY JSON:

{{
  "final_message": "string",
  "chosen_alternatives": []
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
  "final_message": "string",
  "chosen_alternatives": []
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

    original_product = "Regular Milk 1L"

    alternatives = [
        {"name": "Oat Drink 1L", "price": 12, "predicted_success": 0.91, "availability": 100},
        {"name": "Lactose-Free Milk 1.5L", "price": 11, "predicted_success": 0.76, "availability": 870},
        {"name": "Skimmed Milk 1L", "price": 12, "predicted_success": 0.84, "availability": 78},
        {"name": "Whole Milk 1L", "price": 10, "predicted_success": 0.93, "availability": 99},
        {"name": "Banana 1pcs", "price": 1, "predicted_success": 0.9, "availability": 500},  # should be filtered out
    ]

    # First call: get initial alternatives
    start_time = time.time()
    print(model.suggest_substitutions(
        customer_message="bye"
    ))
    end_time = time.time()
    print(f"First call took {end_time - start_time:.2f} seconds")
