import os
from xml.parsers.expat import model

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    api_key=os.getenv('FEATHERLESS_API_KEY'),
    base_url="https://api.featherless.ai/v1",
    model="deepseek-ai/DeepSeek-R1-0528",
)

messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence. Put the final answer in a format like: 'French Translation: <your translation here>'",
    ),
    (
        "human",
        "I love programming."
    ),
]
def strip_think(text: str) -> str:
    # If the model returns <think>...</think>, remove it
    if "<think>" in text and "</think>" in text:
        return text.split("</think>")[-1].strip()
    return text

ai_msg = llm.invoke(messages)
clean = strip_think(ai_msg.content)
print(clean)