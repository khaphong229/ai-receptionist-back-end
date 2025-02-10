import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_response(question):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )
    return response["choices"][0]["message"]["content"]
