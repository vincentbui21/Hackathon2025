AI2_LLM_customer_service
For mention to the customer about the prediction
Function:

suggest_substitutions(prediction_value: float, alternatives: list[str], customer_message: str | None) -> dict

prediction value and alternatives is received from the database

Output:
Type: dict
Output structure is:
{
  "final_message": str,
  "alternatives": list[dict]
}


Example usage:
Example input:
prediction_value = 0.83
alternatives = [
    "Goat Drink 1L: 12€",
    "Lactose-Free Milk 1.5L: 11€",
    "Skimmed Milk 1L: 12€"
]
customer_message = "Do you have other alternatives?"

Example output:
{
  "final_message": "Unfortunately, our Goat Drink 1L is currently out of stock, but perhaps you'd like to try one of these alternatives?",
  "alternatives": [
    {"name": "Goat Drink 1L", "price": 12.0},
    {"name": "Lactose-Free Milk 1.5L", "price": 11.0},
    {"name": "Skimmed Milk 1L", "price": 12.0}
  ]
}

