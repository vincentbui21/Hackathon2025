import os
import time
from langchain_openai import ChatOpenAI

class ValioCustomerServiceLLM:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=os.getenv("FEATHERLESS_API_KEY"),
            base_url="https://api.featherless.ai/v1",
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            timeout=15,
        )

    def suggest_substitutions(self, prediction_value: float, alternatives: list, customer_message: str = None):
        """
        prediction_value: float between 0 and 1.
        alternatives: list of strings containing product name + price, e.g.:
            ["Goat Drink 1L: 12€", "Lactose-Free Milk 1.5L: 11€"]
        """

        alt_list = "\n".join([f"- {item}" for item in alternatives])

        prompt = f"""
You are Valio's helpful and friendly customer support assistant.
Your job is to clearly explain availability and politely suggest alternatives.

RULES:
- DO NOT include chain-of-thought, reasoning, or <think>.
- Keep the tone warm, short, and friendly.
- Always apologize briefly when an item may be unavailable.
- Use "perhaps" to soften suggestions.
- Output ONLY VALID JSON. No markdown, no extra text.
- When extracting price, REMOVE the euro symbol (€) and convert to a numeric value.

The user provided alternatives in the form: "Name: Price€".
Extract them into objects with:
  "name": string,
  "price": number (float)

DATA:
Out-of-stock prediction: {prediction_value}
Raw alternatives:
{alt_list}

Customer message (optional): {customer_message}

Return output EXACTLY in this JSON schema:

{{
  "final_message": "A short friendly message to the customer.",
  "alternatives": [
    {{"name": "string", "price": number}},
    {{"name": "string", "price": number}},
    {{"name": "string", "price": number}}
  ]
}}
"""

        raw_response = self.llm.invoke([("human", prompt)])
        clean = strip_think(raw_response.content)
        return clean


def strip_think(text: str) -> str:
    """Remove any LLM accidental chain-of-thought."""
    if "<think>" in text and "</think>" in text:
        return text.split("</think>")[-1].strip()
    return text.strip()


# Example usage:
model = ValioCustomerServiceLLM()

prediction = 0.83
alternatives = [
    "Goat Drink 1L: 12€",
    "Lactose-Free Milk 1.5L: 11€",
    "Skimmed Milk 1L: 12€"
]

start_time = time.time()
response = model.suggest_substitutions(prediction, alternatives, customer_message="Do you have other alternatives?")
end_time = time.time()

print(response)
print(f"Response time: {end_time - start_time} seconds")
